import { useRef, useState } from "react";
import { t, type EstimateContent } from "@sds/task-library";
import { Prompt, useItemTimer, type ItemProps } from "./common";

/** T10 number line estimate: tap where a number belongs on a line. */
export function EstimateItem({ item, lang, onSubmit, onIdle }: ItemProps) {
  const c = item.content as EstimateContent;
  const timer = useItemTimer(item.id, onIdle);
  const [value, setValue] = useState<number | null>(null);
  const ref = useRef<HTMLDivElement>(null);
  const done = useRef(false);

  const place = (clientX: number) => {
    const box = ref.current!.getBoundingClientRect();
    const frac = Math.min(1, Math.max(0, (clientX - box.left) / box.width));
    const raw = c.min + frac * (c.max - c.min);
    const v = Math.round(raw / c.step) * c.step;
    timer.select(v);
    setValue(v);
  };
  const nudge = (dir: number) => {
    const v = Math.min(c.max, Math.max(c.min, (value ?? (c.min + c.max) / 2) + dir * c.step * Math.max(1, (c.max - c.min) / c.step / 50)));
    timer.select(v);
    setValue(v);
  };
  const frac = value === null ? null : (value - c.min) / (c.max - c.min);
  return (
    <div>
      <Prompt text={t(lang, c.prompt_key, { target: c.target })} lang={lang} />
      <div style={{ padding: "2.5rem 0.5rem 1rem" }}>
        <div
          ref={ref}
          role="slider"
          tabIndex={0}
          aria-valuemin={c.min}
          aria-valuemax={c.max}
          aria-valuenow={value ?? undefined}
          aria-label={t(lang, "place_here")}
          onPointerDown={(e) => place(e.clientX)}
          onKeyDown={(e) => { if (e.key === "ArrowLeft") nudge(-1); if (e.key === "ArrowRight") nudge(1); }}
          style={{ position: "relative", height: 56, cursor: "pointer", touchAction: "none" }}
        >
          <div style={{ position: "absolute", top: 26, left: 0, right: 0, height: 6, background: "#17324d", borderRadius: 3 }} />
          <div style={{ position: "absolute", top: 14, left: 0, width: 4, height: 30, background: "#17324d" }} />
          <div style={{ position: "absolute", top: 14, right: 0, width: 4, height: 30, background: "#17324d" }} />
          {frac !== null && (
            <div style={{ position: "absolute", left: `calc(${frac * 100}% - 14px)`, top: -18 }}>
              <svg width="28" height="44" viewBox="0 0 28 44" aria-hidden="true"><path d="M14 44 L2 18 A14 14 0 1 1 26 18 Z" fill="#e07a1f" /></svg>
            </div>
          )}
        </div>
        <div className="row" style={{ justifyContent: "space-between", fontWeight: 700 }}>
          <span>{c.min}</span>
          <span>{c.max}</span>
        </div>
      </div>
      <div className="row">
        <span className="spacer" />
        <button type="button" className="btn big" disabled={value === null}
          onClick={() => { if (!done.current) { done.current = true; onSubmit({ item, answer: value, timer }); } }}>
          {t(lang, "next")}
        </button>
      </div>
    </div>
  );
}
