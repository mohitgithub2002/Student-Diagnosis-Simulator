import { useEffect, useMemo, useRef, useState } from "react";
import { ItemTimer, t, type BundleItem, type Draft, type FeatureRow, type Lang, type Option } from "@sds/task-library";
import { FigureSvg, Speaker } from "../../components/ui";

export type SubmitFn = (d: Omit<Draft, "timing" | "shownAtEpoch"> & { timer: ItemTimer }) => void;

export interface ItemProps {
  item: BundleItem;
  taskId: string;
  lang: Lang;
  settings: Record<string, any>;
  condition: string;
  onSubmit: SubmitFn;
  onIdle?: (ms: number) => void;
  aux?: Record<string, BundleItem>;
  voiceAllowed?: boolean;
  onFeatures?: (rows: FeatureRow[]) => void;
  previous?: { answer: unknown };
  embedded?: boolean;
  index?: number;
}

/** One timer per shown item; tracks idle time and app/tab switches while the item is on screen. */
export function useItemTimer(key: string, onIdle?: (ms: number) => void): ItemTimer {
  const timer = useMemo(() => new ItemTimer(() => performance.now(), Date.now()), [key]); // eslint-disable-line
  const idleRef = useRef(onIdle);
  idleRef.current = onIdle;
  useEffect(() => {
    const vis = () => timer.visibility(document.hidden);
    const act = () => timer.activity();
    document.addEventListener("visibilitychange", vis);
    window.addEventListener("keydown", act);
    const id = window.setInterval(() => idleRef.current?.(timer.idleNow()), 5000);
    return () => {
      document.removeEventListener("visibilitychange", vis);
      window.removeEventListener("keydown", act);
      window.clearInterval(id);
    };
  }, [timer]);
  return timer;
}

export function promptText(lang: Lang, content: { prompt?: string; prompt_key?: string }, vars: Record<string, string | number> = {}): string {
  return content.prompt ?? (content.prompt_key ? t(lang, content.prompt_key, vars) : "");
}

export function Prompt({ text, lang }: { text: string; lang: Lang }) {
  if (!text) return null;
  return (
    <div className="row" style={{ alignItems: "flex-start", marginBottom: "0.75rem" }}>
      <div className="prompt" style={{ margin: 0, flex: 1 }}>{text}</div>
      <Speaker text={text} lang={lang} />
    </div>
  );
}

export function OptionButton({ option, lang, selected, onClick, disabled }: {
  option: Option; lang: Lang; selected: boolean; onClick: () => void; disabled?: boolean;
}) {
  const label = option.text ?? (option.label_key ? t(lang, option.label_key) : option.id);
  return (
    <button type="button" className={`opt ${option.figure ? "figure-opt" : "text"} ${selected ? "selected" : ""}`}
      aria-pressed={selected} onClick={onClick} disabled={disabled}>
      {option.figure ? <FigureSvg figure={option.figure} size={84} /> : <span>{label}</span>}
    </button>
  );
}

export function Countdown({ seconds, onEnd, label }: { seconds: number; onEnd: () => void; label?: (s: number) => string }) {
  const [left, setLeft] = useState(seconds);
  const endRef = useRef(onEnd);
  endRef.current = onEnd;
  useEffect(() => {
    const start = performance.now();
    const id = window.setInterval(() => {
      const remaining = Math.max(0, seconds - (performance.now() - start) / 1000);
      setLeft(remaining);
      if (remaining <= 0) {
        window.clearInterval(id);
        endRef.current();
      }
    }, 200);
    return () => window.clearInterval(id);
  }, [seconds]);
  return <span className="timer" aria-live="off">{label ? label(Math.ceil(left)) : `${Math.ceil(left)}s`}</span>;
}
