import { useEffect, useRef, useState, type ReactNode } from "react";
import { Pressable, StyleSheet, Text, View, type StyleProp, type ViewStyle } from "react-native";
import Svg, { Circle, Defs, Path, Pattern, Rect } from "react-native-svg";
import { figurePrims, type Figure } from "@sds/task-library";

export const C = {
  ink: "#1d2733", muted: "#6b7785", line: "#d9e1ea", bg: "#eef3f8", panel: "#ffffff", brand: "#17324d",
  brand2: "#2f6f9f", accent: "#f2c14e", good: "#2e7d4f", grow: "#a5651a", danger: "#b42318",
};

export function Btn({ title, onPress, disabled, kind = "primary", big, style }: {
  title: string; onPress: () => void; disabled?: boolean; kind?: "primary" | "secondary" | "ghost" | "danger"; big?: boolean;
  style?: StyleProp<ViewStyle>;
}) {
  const bg = kind === "primary" ? C.brand : kind === "danger" ? C.danger : "transparent";
  const fg = kind === "primary" || kind === "danger" ? "#fff" : C.brand;
  return (
    <Pressable accessibilityRole="button" accessibilityState={{ disabled }} onPress={disabled ? undefined : onPress}
      style={({ pressed }) => [s.btn, { backgroundColor: bg, borderColor: kind === "ghost" ? "transparent" : C.brand,
        opacity: disabled ? 0.45 : pressed ? 0.85 : 1, minHeight: big ? 64 : 52 }, style]}>
      <Text style={[s.btnText, { color: fg, fontSize: big ? 20 : 17 }]}>{title}</Text>
    </Pressable>
  );
}

export function Card({ children, style }: { children: ReactNode; style?: StyleProp<ViewStyle> }) {
  return <View style={[s.card, style]}>{children}</View>;
}

export function Opt({ label, selected, onPress, children }: { label?: string; selected: boolean; onPress: () => void; children?: ReactNode }) {
  return (
    <Pressable accessibilityRole="button" accessibilityState={{ selected }} accessibilityLabel={label} onPress={onPress}
      style={[s.opt, selected && s.optSelected]}>
      {children ?? <Text style={s.optText}>{label}</Text>}
      {selected && <Text style={{ color: C.brand2, fontWeight: "800", marginLeft: 8 }}>✓</Text>}
    </Pressable>
  );
}

export function H1({ children }: { children: ReactNode }) {
  return <Text style={s.h1}>{children}</Text>;
}

export function P({ children, muted, big }: { children: ReactNode; muted?: boolean; big?: boolean }) {
  return <Text style={[s.p, muted && { color: C.muted }, big && { fontSize: 20, fontWeight: "700", color: C.brand }]}>{children}</Text>;
}

/** Counts down and calls onEnd once at zero. Hidden countdowns still run (a safety stop without a visible clock). */
export function Countdown({ seconds, onEnd, label, hidden }: {
  seconds: number; onEnd: () => void; label: (s: number) => string; hidden?: boolean;
}) {
  const [left, setLeft] = useState(seconds);
  const endRef = useRef(onEnd);
  endRef.current = onEnd;
  useEffect(() => {
    const start = Date.now();
    const id = setInterval(() => {
      const remaining = Math.max(0, seconds - (Date.now() - start) / 1000);
      setLeft(remaining);
      if (remaining <= 0) {
        clearInterval(id);
        endRef.current();
      }
    }, 250);
    return () => clearInterval(id);
  }, [seconds]);
  if (hidden) return null;
  return <Text style={{ color: C.muted, fontWeight: "700" }}>{label(Math.ceil(left))}</Text>;
}

/** Microphone level meter on a decibel scale (-60 dB to 0 dB), so quiet Android input still moves it. */
export function LevelBar({ level }: { level: number }) {
  const db = level > 0 ? 20 * Math.log10(level) : -100;
  const pct = Math.max(0, Math.min(100, ((db + 60) / 60) * 100));
  return (
    <View style={{ height: 12, borderRadius: 6, backgroundColor: C.line, overflow: "hidden" }}
      accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
      <View style={{ width: `${pct}%`, height: "100%", backgroundColor: C.brand2 }} />
    </View>
  );
}

/** Figures from the shared geometry; stripes and dots are patterns, so colour is never the only cue. */
export function FigureView({ figure, size = 84 }: { figure: Figure; size?: number }) {
  const prims = figurePrims(figure, C.brand);
  return (
    <Svg width={size} height={size} viewBox="0 0 100 100" accessibilityLabel={`${figure.fill} ${figure.shape}`}>
      <Defs>
        <Pattern id="sds-stripes" width="10" height="10" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
          <Rect width="10" height="10" fill="#fff" />
          <Rect width="4" height="10" fill={C.brand} />
        </Pattern>
        <Pattern id="sds-dots" width="12" height="12" patternUnits="userSpaceOnUse">
          <Rect width="12" height="12" fill="#fff" />
          <Circle cx="6" cy="6" r="3" fill={C.brand} />
        </Pattern>
      </Defs>
      {prims.map((p, i) => {
        const a = camel(p.attrs);
        if (p.tag === "circle") return <Circle key={i} {...(a as any)} />;
        return <Path key={i} {...(a as any)} />;
      })}
    </Svg>
  );
}

function camel(attrs: Record<string, string | number>): Record<string, string | number> {
  return Object.fromEntries(Object.entries(attrs).map(([k, v]) => [k.replace(/-(\w)/g, (_, c) => c.toUpperCase()), v]));
}

export const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: C.bg },
  scroll: { padding: 16, gap: 12 },
  btn: { borderWidth: 2, borderRadius: 14, paddingHorizontal: 18, alignItems: "center", justifyContent: "center" },
  btnText: { fontWeight: "700" },
  card: { backgroundColor: C.panel, borderRadius: 18, padding: 16, borderWidth: 1, borderColor: C.line, gap: 10 },
  opt: { minHeight: 60, borderWidth: 3, borderColor: C.line, borderRadius: 16, backgroundColor: "#fff", padding: 12,
    flexDirection: "row", alignItems: "center", justifyContent: "center" },
  optSelected: { borderColor: C.brand2, backgroundColor: "#eaf2fb" },
  optText: { fontSize: 18, color: C.ink, flexShrink: 1 },
  h1: { fontSize: 26, fontWeight: "800", color: C.brand },
  p: { fontSize: 17, color: C.ink, lineHeight: 25 },
  input: { borderWidth: 2, borderColor: C.line, borderRadius: 12, padding: 12, fontSize: 18, backgroundColor: "#fff" },
  row: { flexDirection: "row", gap: 10, alignItems: "center", flexWrap: "wrap" },
  passage: { backgroundColor: "#fffdf7", borderColor: "#efe6d2", borderWidth: 1, borderRadius: 14, padding: 14 },
});
