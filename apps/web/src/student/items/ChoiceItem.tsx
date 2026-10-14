import { useEffect, useRef, useState } from "react";
import { checkAnswer, dotLayout, t, type ChoiceContent, type Figure, type Lang } from "@sds/task-library";
import { FigureSvg } from "../../components/ui";
import { OptionButton, Prompt, promptText, useItemTimer, type ItemProps } from "./common";

/**
 * Multiple choice in every layout: clue chains (T5, T23), shape puzzles (T6), quick pairs (T4, T10, T17),
 * word meaning (T9), worked plans (T15), symbol codes (T18, T19). Also handles the special behaviour of
 * Very Hard Puzzles (keep trying), Feedback Reaction (retry offer), the pressure timer and answer review.
 */
export function ChoiceItem(props: ItemProps) {
  const { item, lang, taskId, settings, onSubmit, previous } = props;
  const c = item.content as ChoiceContent;
  const timer = useItemTimer(`${item.id}:${props.condition}`, props.onIdle);
  const [selected, setSelected] = useState<string | null>(previous ? String(previous.answer ?? "") || null : null);
  const [hidden, setHidden] = useState(false);
  const [attempts, setAttempts] = useState(1);
  const [notYet, setNotYet] = useState(false);
  const [feedback, setFeedback] = useState<null | { variant: string; first: string }>(null);
  const done = useRef(false);
  const immediate = c.layout === "pair" && !previous;
  const persist = taskId === "T19";
  const retryTask = taskId === "T20";
  const pressure = Boolean(settings.pressure);

  useEffect(() => {
    if (previous?.answer != null) timer.select(String(previous.answer));
    if (c.show_ms) {
      const id = window.setTimeout(() => setHidden(true), c.show_ms);
      return () => window.clearTimeout(id);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const finish = (answer: string | null, extra: Record<string, unknown> = {}, opts: { skipped?: boolean; retries?: number } = {}) => {
    if (done.current) return;
    done.current = true;
    onSubmit({
      item, answer, timer, extra, skipped: opts.skipped, retries: opts.retries,
      askConfidence: previous ? false : undefined,
    });
  };

  const choose = (id: string) => {
    timer.select(id);
    setSelected(id);
    setNotYet(false);
    if (immediate && !feedback) finish(id);
  };

  const next = () => {
    if (!selected) return;
    const correct = checkAnswer(item, selected);
    if (persist) {
      if (correct) finish(selected, { attempts, gave_up: false });
      else {
        setAttempts((a) => a + 1);
        setNotYet(true);
      }
      return;
    }
    if (retryTask) {
      if (feedback) {
        finish(feedback.first, {
          retry_offered: true, feedback_variant: feedback.variant, retried: true,
          retry_correct: checkAnswer(item, selected) === true,
        }, { retries: 1 });
      } else if (correct === false) {
        const variants: string[] = settings.feedback_variants ?? ["effort", "ability", "neutral"];
        const n = Number(sessionStorage.getItem("sds.t20") ?? "0");
        sessionStorage.setItem("sds.t20", String(n + 1));
        setFeedback({ variant: variants[n % variants.length], first: selected });
        setSelected(null);
      } else finish(selected);
      return;
    }
    finish(selected);
  };

  const declineRetry = () => {
    if (feedback) finish(feedback.first, { retry_offered: true, feedback_variant: feedback.variant, retried: false });
  };

  const layoutClass = c.layout === "pair" ? "pair" : c.layout === "grid" ? "grid" : "";
  return (
    <div>
      {pressure && <PressureBar seconds={settings.pressure_seconds ?? 12} onEnd={() => finish(null, { timeout: true }, { skipped: true })} />}
      {previous && <p className="alert">{t(lang, "review.text")}</p>}
      <Prompt text={promptText(lang, c)} lang={lang} />
      <Stem content={c} lang={lang} hidden={hidden} />
      {feedback && (
        <div className="alert" role="status" style={{ marginBottom: "0.75rem" }}>
          <strong>{t(lang, `t20.${feedback.variant}`)}</strong> {t(lang, "t20.retry")}
        </div>
      )}
      {notYet && <div className="alert" role="status" style={{ marginBottom: "0.75rem" }}>{t(lang, "t19.not_yet")}</div>}
      <div className={`options ${layoutClass}`}>
        {c.options.map((o) => (
          <OptionButton key={o.id} option={o} lang={lang} selected={selected === o.id} onClick={() => choose(o.id)} />
        ))}
      </div>
      {!immediate && (
        <div className="row" style={{ marginTop: "1rem" }}>
          {persist && (
            <button type="button" className="btn secondary" onClick={() => finish(selected, { attempts, gave_up: true })}>
              {t(lang, "t19.move_on")}
            </button>
          )}
          {feedback && (
            <button type="button" className="btn secondary" onClick={declineRetry}>{t(lang, "next")}</button>
          )}
          <span className="spacer" />
          <button type="button" className="btn big" disabled={!selected} onClick={next}>
            {feedback ? t(lang, "submit") : previous ? (selected === String(previous.answer) ? t(lang, "keep") : t(lang, "next")) : t(lang, "next")}
          </button>
        </div>
      )}
      {persist && <PersistClock onEnd={() => finish(selected, { attempts, gave_up: true })} />}
    </div>
  );
}

function PersistClock({ onEnd }: { onEnd: () => void }) {
  useEffect(() => {
    const id = window.setTimeout(onEnd, 90_000);
    return () => window.clearTimeout(id);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps
  return null;
}

function PressureBar({ seconds, onEnd }: { seconds: number; onEnd: () => void }) {
  const [frac, setFrac] = useState(0);
  const endRef = useRef(onEnd);
  endRef.current = onEnd;
  useEffect(() => {
    const start = performance.now();
    const id = window.setInterval(() => {
      const f = Math.min(1, (performance.now() - start) / (seconds * 1000));
      setFrac(f);
      if (f >= 1) {
        window.clearInterval(id);
        endRef.current();
      }
    }, 100);
    return () => window.clearInterval(id);
  }, [seconds]);
  return (
    <div aria-label="Time" role="progressbar" aria-valuemin={0} aria-valuemax={seconds} aria-valuenow={Math.round(frac * seconds)}>
      <div className="pressure-bar"><span style={{ width: `${frac * 100}%` }} /></div>
    </div>
  );
}

function Stem({ content, lang, hidden }: { content: ChoiceContent; lang: Lang; hidden: boolean }) {
  const s = (content.stem ?? {}) as Record<string, any>;
  if (s.rules) {
    return (
      <div className="rules">
        <ol>{(s.rules as string[]).map((r, i) => <li key={i}>{r}</li>)}</ol>
        <p style={{ margin: 0 }}><strong>{s.fact}</strong></p>
      </div>
    );
  }
  if (s.figures) {
    return (
      <div className="stem-figures">
        {(s.figures as Figure[]).map((f, i) => <FigureSvg key={i} figure={f} size={90} />)}
        {s.blank && <div className="slot" aria-label="What comes next">?</div>}
      </div>
    );
  }
  if (s.left && s.right) {
    return (
      <div className="options pair" style={{ marginBottom: "1rem" }}>
        <PairSide side={s.left} hidden={hidden} label={t(lang, "left")} />
        <PairSide side={s.right} hidden={hidden} label={t(lang, "right")} />
      </div>
    );
  }
  if (s.sentence) {
    const parts = String(s.sentence).split(String(s.word));
    return (
      <p className="passage" style={{ marginBottom: "1rem" }}>
        {parts.map((p, i) => (
          <span key={i}>{p}{i < parts.length - 1 && <u><strong>{s.word}</strong></u>}</span>
        ))}
      </p>
    );
  }
  if (s.steps) {
    return (
      <div className="rules">
        <p><strong>{s.setup}</strong></p>
        <ol>{(s.steps as string[]).map((st, i) => <li key={i}>{st}</li>)}</ol>
      </div>
    );
  }
  if (s.equations) {
    const icon = (shape: string) => <FigureSvg figure={{ shape, rotation: 0, count: 1, fill: "solid" }} size={36} label={shape} />;
    return (
      <div className="rules" style={{ fontSize: "1.4rem" }}>
        {(s.equations as { terms: string[]; total: number }[]).map((eq, i) => (
          <div key={i} className="row" style={{ gap: "0.4rem" }}>
            {eq.terms.map((term, j) => <span key={j} className="row" style={{ gap: "0.4rem" }}>{j > 0 && "+"}{icon(term)}</span>)}
            <span>= {eq.total}</span>
          </div>
        ))}
        <div className="row" style={{ gap: "0.4rem", marginTop: "0.5rem" }}>{icon(s.ask)} <span>= ?</span></div>
      </div>
    );
  }
  return null;
}

function PairSide({ side, hidden, label }: { side: Record<string, any>; hidden: boolean; label: string }) {
  let body: React.ReactNode = null;
  if (side.figure) body = <FigureSvg figure={side.figure} size={110} />;
  else if (side.text) body = <span style={{ fontSize: "2rem", fontWeight: 800, letterSpacing: "0.2em" }}>{side.text}</span>;
  else if (side.dots !== undefined) {
    body = hidden ? <span className="muted">●●●</span> : (
      <svg viewBox="0 0 100 100" width="100%" style={{ maxWidth: 180 }} role="img" aria-label={`${label}: dots`}>
        {dotLayout(side.dots, side.seed).map((d, i) => <circle key={i} cx={d.x * 100} cy={d.y * 100} r={3.6} fill="currentColor" />)}
      </svg>
    );
  } else if (side.prices) {
    body = (
      <div style={{ fontSize: "1.3rem", fontWeight: 700 }}>
        {(side.prices as number[]).map((p, i) => <div key={i}>₹{p}</div>)}
      </div>
    );
  }
  return (
    <div className="card center" aria-label={label} style={{ minHeight: 150, display: "grid", placeItems: "center" }}>
      {body}
    </div>
  );
}
