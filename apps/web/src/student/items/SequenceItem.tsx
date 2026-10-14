import { useEffect, useRef, useState } from "react";
import { TOKEN_COLORS, t, type SequenceContent } from "@sds/task-library";
import { FigureSvg } from "../../components/ui";
import { Prompt, useItemTimer, type ItemProps } from "./common";

/** T1 Sequence Recall: watch digits, symbols or colours one at a time, then tap them back. */
export function SequenceItem({ item, lang, onSubmit, onIdle }: ItemProps) {
  const c = item.content as SequenceContent;
  const [shown, setShown] = useState<number>(-1); // index being shown; -1 = get ready; >= length = input phase
  const [answer, setAnswer] = useState<string[]>([]);
  const [undos, setUndos] = useState(0);
  const timer = useItemTimer(`${item.id}:input:${shown >= c.sequence.length}`, onIdle);
  const done = useRef(false);

  useEffect(() => {
    let i = -1;
    let id: number;
    const step = () => {
      i += 1;
      setShown(i * 2); // even = token visible, odd = gap
      if (i < c.sequence.length) {
        id = window.setTimeout(() => {
          setShown(i * 2 + 1);
          id = window.setTimeout(step, c.gap_ms);
        }, c.show_ms);
      } else setShown(c.sequence.length * 2);
    };
    id = window.setTimeout(step, 900);
    return () => window.clearTimeout(id);
  }, [c]);

  const inputPhase = shown >= c.sequence.length * 2;
  const tap = (tok: string) => {
    if (answer.length >= c.sequence.length) return;
    timer.activity();
    setAnswer((a) => [...a, tok]);
  };
  const submit = () => {
    if (done.current) return;
    done.current = true;
    onSubmit({ item, answer, timer, extra: { undos } });
  };

  if (!inputPhase) {
    const visible = shown >= 0 && shown % 2 === 0 ? c.sequence[shown / 2] : null;
    return (
      <div className="center">
        <p className="prompt">{t(lang, "t1.watch")}</p>
        <div style={{ display: "grid", placeItems: "center", minHeight: 200 }} aria-live="polite">
          {visible ? <Token mode={c.mode} tok={visible} big /> : <div className="token" aria-hidden="true" />}
        </div>
      </div>
    );
  }
  return (
    <div>
      <Prompt text={t(lang, c.direction === "backward" ? "t1.backward" : "t1.forward")} lang={lang} />
      <div className="answer-row" aria-label="Your answer">
        {answer.map((tok, i) => <Token key={i} mode={c.mode} tok={tok} />)}
      </div>
      <div className="keypad">
        {c.choices.map((tok) => (
          <button key={tok} type="button" onClick={() => tap(tok)} aria-label={tok}>
            <Token mode={c.mode} tok={tok} inline />
          </button>
        ))}
      </div>
      <div className="row" style={{ marginTop: "1rem" }}>
        <button type="button" className="btn secondary" disabled={!answer.length}
          onClick={() => { timer.activity(); setUndos((u) => u + 1); setAnswer((a) => a.slice(0, -1)); }}>
          {t(lang, "undo")}
        </button>
        <span className="spacer" />
        <button type="button" className="btn big" disabled={answer.length !== c.sequence.length} onClick={submit}>
          {t(lang, "next")}
        </button>
      </div>
    </div>
  );
}

function Token({ mode, tok, big, inline }: { mode: SequenceContent["mode"]; tok: string; big?: boolean; inline?: boolean }) {
  const size = big ? 120 : inline ? 44 : 40;
  if (mode === "digits") {
    return inline ? <span>{tok}</span> : <div className={big ? "token" : "mini"} style={big ? { width: 140, height: 140, fontSize: "4rem" } : undefined}>{tok}</div>;
  }
  if (mode === "colors") {
    return (
      <span style={{ display: "inline-flex", flexDirection: "column", alignItems: "center", fontSize: big ? "1rem" : "0.65rem" }}>
        <svg width={size} height={size} viewBox="0 0 40 40" aria-hidden="true"><circle cx="20" cy="20" r="17" fill={TOKEN_COLORS[tok]} stroke="#1d2733" strokeWidth="1.5" /></svg>
        <span>{tok}</span>
      </span>
    );
  }
  return <FigureSvg figure={{ shape: tok, rotation: 0, count: 1, fill: "solid" }} size={size} label={tok} />;
}
