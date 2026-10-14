import { useEffect, useMemo, useRef, useState } from "react";
import { streamSequence, t, type StreamContent } from "@sds/task-library";
import { FigureSvg } from "../../components/ui";
import { useItemTimer, type ItemProps } from "./common";

/**
 * T3 Focus Stream: one minute per block. Shapes appear one by one; tap only for the target. The stream
 * comes from the item's seed, so the server can regenerate it and score hits and false alarms.
 */
export function StreamItem({ item, lang, onSubmit, index: position = 1 }: ItemProps) {
  const c = item.content as StreamContent;
  const stimuli = useMemo(() => streamSequence(c), [c]);
  const timer = useItemTimer(item.id); // no idle pause prompt: watching without tapping is the task
  // Blocks after the first run back to back, so the four minutes measure focus over time.
  const [phase, setPhase] = useState<"ready" | "run">(position > 1 ? "run" : "ready");
  const [index, setIndex] = useState(-1);
  const [visible, setVisible] = useState(false);
  const taps = useRef<{ i: number; rt: number }[]>([]);
  const onset = useRef(0);
  const current = useRef(-1);
  const done = useRef(false);

  useEffect(() => {
    if (phase !== "run") return;
    let i = -1;
    const timers: number[] = [];
    const tick = () => {
      i += 1;
      if (i >= stimuli.length) {
        if (!done.current) {
          done.current = true;
          onSubmit({ item, answer: { taps: taps.current }, timer, extra: { block: position } });
        }
        return;
      }
      current.current = i;
      onset.current = performance.now();
      setIndex(i);
      setVisible(true);
      timers.push(window.setTimeout(() => setVisible(false), c.stim_ms));
      timers.push(window.setTimeout(tick, c.isi_ms));
    };
    timers.push(window.setTimeout(tick, 600));
    return () => timers.forEach((id) => window.clearTimeout(id));
  }, [phase]); // eslint-disable-line react-hooks/exhaustive-deps

  const tap = () => {
    const i = current.current;
    if (i < 0 || taps.current.some((x) => x.i === i)) return;
    timer.activity();
    taps.current.push({ i, rt: Math.round(performance.now() - onset.current) });
  };

  useEffect(() => {
    if (phase !== "run") return;
    const key = (e: KeyboardEvent) => { if (e.code === "Space") { e.preventDefault(); tap(); } };
    window.addEventListener("keydown", key);
    return () => window.removeEventListener("keydown", key);
  }, [phase]); // eslint-disable-line react-hooks/exhaustive-deps

  if (phase === "ready") {
    return (
      <div className="center stack">
        <p className="prompt">{t(lang, c.prompt_key)}</p>
        <div style={{ display: "grid", placeItems: "center" }}><FigureSvg figure={c.target} size={140} /></div>
        <button type="button" className="btn big" onClick={() => setPhase("run")}>{t(lang, "start")}</button>
      </div>
    );
  }
  const stim = index >= 0 ? stimuli[index] : null;
  return (
    <div>
      <div className="row small muted" style={{ justifyContent: "space-between" }}>
        <span>{t(lang, "t3.tap_target")}</span>
        <FigureSvg figure={c.target} size={32} />
      </div>
      <div className="stream-box" aria-hidden="true">
        {stim && visible ? <FigureSvg figure={stim.figure} size={170} /> : null}
      </div>
      <button type="button" className="tap-pad" onPointerDown={tap}>{t(lang, "t3.tap_here")}</button>
    </div>
  );
}
