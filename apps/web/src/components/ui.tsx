import { useEffect, useState, type ReactNode } from "react";
import { Link, NavLink } from "react-router-dom";
import { figurePrims, type Figure } from "@sds/task-library";

export function Topbar({ title, links, right }: { title: string; links?: { to: string; label: string }[]; right?: ReactNode }) {
  return (
    <header className="topbar">
      <div className="inner">
        <Link to="/" className="brand" aria-label="Home">
          <Logo /> {title}
        </Link>
        <nav aria-label="Main">
          {links?.map((l) => (
            <NavLink key={l.to} to={l.to} end>
              {l.label}
            </NavLink>
          ))}
          {right}
        </nav>
      </div>
    </header>
  );
}

export function Logo({ size = 26 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" aria-hidden="true">
      <rect width="64" height="64" rx="14" fill="#fff" opacity="0.15" />
      <path d="M32 12 L37 26 L52 26 L40 35 L45 50 L32 41 L19 50 L24 35 L12 26 L27 26 Z" fill="#f2c14e" />
    </svg>
  );
}

export function Alert({ kind = "info", children }: { kind?: "info" | "error" | "ok"; children: ReactNode }) {
  if (!children) return null;
  return (
    <div className={`alert ${kind === "info" ? "" : kind}`} role={kind === "error" ? "alert" : "status"}>
      {children}
    </div>
  );
}

export function Field({ label, children, hint }: { label: string; children: ReactNode; hint?: string }) {
  return (
    <label className="field">
      <span>{label}</span>
      {children}
      {hint && <small className="muted">{hint}</small>}
    </label>
  );
}

export function Loading({ text = "Loading…" }: { text?: string }) {
  return <p className="muted" role="status">{text}</p>;
}

/** Shared SVG patterns for striped and dotted fills (used by every figure on the page). */
export function SvgDefs() {
  return (
    <svg width="0" height="0" style={{ position: "absolute" }} aria-hidden="true">
      <defs>
        <pattern id="sds-stripes" width="10" height="10" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
          <rect width="10" height="10" fill="#fff" />
          <rect width="4" height="10" fill="currentColor" />
        </pattern>
        <pattern id="sds-dots" width="12" height="12" patternUnits="userSpaceOnUse">
          <rect width="12" height="12" fill="#fff" />
          <circle cx="6" cy="6" r="3" fill="currentColor" />
        </pattern>
      </defs>
    </svg>
  );
}

export function FigureSvg({ figure, size = 84, label }: { figure: Figure; size?: number; label?: string }) {
  const prims = figurePrims(figure);
  return (
    <svg className="figure" width={size} height={size} viewBox="0 0 100 100" role="img" aria-label={label ?? describeFigure(figure)}>
      {prims.map((p, i) => {
        const Tag = p.tag as any;
        return <Tag key={i} {...camel(p.attrs)} />;
      })}
    </svg>
  );
}

function camel(attrs: Record<string, string | number>): Record<string, string | number> {
  return Object.fromEntries(Object.entries(attrs).map(([k, v]) => [k.replace(/-(\w)/g, (_, c) => c.toUpperCase()), v]));
}

export function describeFigure(f: Figure): string {
  const count = f.count > 1 ? `${f.count} ` : "";
  return `${count}${f.fill} ${f.shape}${f.count > 1 ? "s" : ""}, turned ${f.rotation} degrees`;
}

export function useAsync<T>(fn: () => Promise<T>, deps: unknown[]): { data: T | null; error: unknown; loading: boolean; reload: () => void } {
  const [state, setState] = useState<{ data: T | null; error: unknown; loading: boolean }>({ data: null, error: null, loading: true });
  const [tick, setTick] = useState(0);
  useEffect(() => {
    let alive = true;
    setState((s) => ({ ...s, loading: true }));
    fn().then(
      (data) => alive && setState({ data, error: null, loading: false }),
      (error) => alive && setState({ data: null, error, loading: false }),
    );
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick]);
  return { ...state, reload: () => setTick((t) => t + 1) };
}

export function Speaker({ text, lang }: { text: string; lang: string }) {
  return (
    <button type="button" className="speaker" onClick={() => speak(text, lang)} aria-label="Read aloud" title="Read aloud">
      <svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true">
        <path d="M4 9h4l5-4v14l-5-4H4z" fill="currentColor" />
        <path d="M16 8.5a5 5 0 0 1 0 7M18.5 6a8.5 8.5 0 0 1 0 12" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" />
      </svg>
    </button>
  );
}

/** Audio prompts for instructions (accessibility). Prefers voices that run on the device. */
export function speak(text: string, lang: string): void {
  if (!("speechSynthesis" in window)) return;
  const u = new SpeechSynthesisUtterance(text);
  u.lang = lang === "hi" ? "hi-IN" : "en-IN";
  const voices = window.speechSynthesis.getVoices().filter((v) => v.lang.startsWith(lang === "hi" ? "hi" : "en"));
  u.voice = voices.find((v) => v.localService) ?? voices[0] ?? null;
  u.rate = 0.95;
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(u);
}

export function formatDate(iso: string | null | undefined, lang = "en"): string {
  if (!iso) return "";
  const d = new Date(iso.length === 10 ? `${iso}T00:00:00` : iso);
  return d.toLocaleDateString(lang === "hi" ? "hi-IN" : "en-IN", { day: "numeric", month: "short" });
}
