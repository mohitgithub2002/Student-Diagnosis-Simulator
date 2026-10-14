import { useEffect, useRef, useState } from "react";
import { ItemTimer, t, type BundleItem, type Lang, type PassageQuestionsContent, type Question } from "@sds/task-library";
import { Speaker } from "../../components/ui";
import { ChoiceItem } from "./ChoiceItem";
import { Countdown, OptionButton, Prompt, type ItemProps } from "./common";

type Phase =
  | { kind: "study"; recap?: boolean }
  | { kind: "distractor"; i: number }
  | { kind: "questions"; i: number };

/**
 * Card, passage or mini-lesson followed by questions: Delayed Recall (T2), Passage and Inference (T8),
 * Mini-Lesson (T12). Logs a study event, then one event per question (each with its own timing).
 */
export function PassageItem(props: ItemProps) {
  const { item, lang, settings, onSubmit, onIdle, aux = {} } = props;
  const c = item.content as PassageQuestionsContent;
  const delayed = settings.phase === "delayed";
  const distractorIds: string[] = (settings.distractor_ids ?? []).filter((id: string) => id in aux);
  const setA = c.questions.filter((q) => (q.set ?? "A") === "A");
  const setB = c.questions.filter((q) => q.set === "B");
  const [phase, setPhase] = useState<Phase>(delayed ? { kind: "questions", i: 0 } : { kind: "study" });
  const [rereads, setRereads] = useState(0);
  const [peek, setPeek] = useState(false);
  const studyTimer = useRef(new ItemTimer(() => performance.now(), Date.now()));

  const order = c.mode === "lesson" ? [...setA, ...setB] : c.questions;

  const finishStudy = (recap = false) => {
    onSubmit({ item, answer: null, timer: studyTimer.current, final: false, askConfidence: false,
      extra: { phase: recap ? "recap" : "study" } });
    studyTimer.current = new ItemTimer(() => performance.now(), Date.now());
    if (recap) setPhase({ kind: "questions", i: setA.length });
    else if (distractorIds.length && c.mode === "card") setPhase({ kind: "distractor", i: 0 });
    else setPhase({ kind: "questions", i: 0 });
  };

  if (phase.kind === "study") {
    const minSeconds = c.mode === "lesson" ? (phase.recap ? 10 : 60) : c.mode === "card" ? 15 : 0;
    return (
      <StudyScreen c={c} lang={lang} recap={phase.recap} minSeconds={minSeconds}
        maxSeconds={phase.recap ? c.recap?.study_s ?? 30 : c.study_s ?? 0} onDone={() => finishStudy(phase.recap)} />
    );
  }

  if (phase.kind === "distractor") {
    const ref = distractorIds[phase.i];
    const sub = aux[ref] as BundleItem;
    return (
      <div>
        <p className="badge">{t(lang, "card.quick_round")}</p>
        <ChoiceItem key={ref} {...props} item={sub} taskId="T4" condition="t2_distractor" settings={{}}
          onSubmit={(d) => {
            onSubmit({ ...d, condition: "t2_distractor", final: false, askConfidence: false });
            setPhase(phase.i + 1 < distractorIds.length ? { kind: "distractor", i: phase.i + 1 } : { kind: "questions", i: 0 });
          }} />
      </div>
    );
  }

  const q = order[phase.i];
  if (!q) return null;
  return (
    <div>
      {c.mode === "passage" && (
        <div className="row" style={{ marginBottom: "0.5rem" }}>
          <span className="badge">{t(lang, "of", { a: phase.i + 1, b: order.length })}</span>
          <span className="spacer" />
          <button type="button" className="btn secondary" onClick={() => { setPeek((p) => !p); if (!peek) setRereads((r) => r + 1); }}>
            {t(lang, "read_again")}
          </button>
        </div>
      )}
      {peek && c.passage && <p className="passage">{c.passage.text}</p>}
      {c.mode !== "passage" && <p className="muted small">{t(lang, c.mode === "lesson" ? "lesson.questions" : "card.questions")}</p>}
      <QuestionView key={`${q.id}`} q={q} lang={lang} onIdle={onIdle}
        onAnswer={(answer, timer) => {
          const last = phase.i === order.length - 1;
          onSubmit({ item, answer, timer, final: last,
            extra: { qid: q.id, qtype: q.qtype, set: q.set, rereads: c.mode === "passage" ? rereads : undefined } });
          setPeek(false);
          setRereads(0);
          if (!last) {
            if (c.mode === "lesson" && phase.i + 1 === setA.length && c.recap) setPhase({ kind: "study", recap: true });
            else setPhase({ kind: "questions", i: phase.i + 1 });
          }
        }} />
    </div>
  );
}

function StudyScreen({ c, lang, recap, minSeconds, maxSeconds, onDone }: {
  c: PassageQuestionsContent; lang: Lang; recap?: boolean; minSeconds: number; maxSeconds: number; onDone: () => void;
}) {
  const [canGo, setCanGo] = useState(minSeconds === 0);
  const fired = useRef(false);
  const done = () => {
    if (!fired.current) {
      fired.current = true;
      onDone();
    }
  };
  useEffect(() => {
    if (minSeconds > 0) {
      const id = window.setTimeout(() => setCanGo(true), minSeconds * 1000);
      return () => window.clearTimeout(id);
    }
  }, [minSeconds]);
  let body: React.ReactNode;
  let heading = "";
  let speech = "";
  if (recap && c.recap) {
    heading = t(lang, "lesson.recap");
    speech = c.recap.text;
    body = <p className="passage">{c.recap.text}</p>;
  } else if (c.mode === "card" && c.card) {
    heading = t(lang, "card.study");
    speech = c.card.lines.join(". ");
    body = (
      <div className="passage">
        <h3>{c.card.title}</h3>
        <ul>{c.card.lines.map((l, i) => <li key={i}>{l}</li>)}</ul>
      </div>
    );
  } else if (c.mode === "lesson" && c.lesson) {
    heading = t(lang, "lesson.learn");
    speech = c.lesson.sections.join(" ");
    body = (
      <div className="passage">
        <h3>{c.lesson.title}</h3>
        {c.lesson.sections.map((s, i) => <p key={i}>{s}</p>)}
      </div>
    );
  } else if (c.passage) {
    heading = t(lang, "passage.read");
    body = (
      <div className="passage">
        <h3>{c.passage.title}</h3>
        <p>{c.passage.text}</p>
      </div>
    );
  }
  return (
    <div className="stack">
      <div className="row">
        <strong className="prompt" style={{ margin: 0, flex: 1 }}>{heading}</strong>
        {speech && c.mode !== "passage" && <Speaker text={speech} lang={lang} />}
        {maxSeconds > 0 && <Countdown seconds={maxSeconds} onEnd={done} label={(s) => t(lang, "seconds_left", { s })} />}
      </div>
      {body}
      <div className="row">
        <span className="spacer" />
        <button type="button" className="btn big" disabled={!canGo} onClick={done}>
          {c.mode === "passage" ? t(lang, "done_reading") : t(lang, "ready")}
        </button>
      </div>
    </div>
  );
}

function QuestionView({ q, lang, onAnswer, onIdle }: {
  q: Question; lang: Lang; onAnswer: (answer: string, timer: ItemTimer) => void; onIdle?: (ms: number) => void;
}) {
  const timer = useRef(new ItemTimer(() => performance.now(), Date.now())).current;
  const [selected, setSelected] = useState<string | null>(null);
  const sent = useRef(false);
  useEffect(() => {
    const id = window.setInterval(() => onIdle?.(timer.idleNow()), 5000);
    const vis = () => timer.visibility(document.hidden);
    document.addEventListener("visibilitychange", vis);
    return () => {
      window.clearInterval(id);
      document.removeEventListener("visibilitychange", vis);
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps
  return (
    <div>
      <Prompt text={q.prompt} lang={lang} />
      <div className="options">
        {q.options.map((o) => (
          <OptionButton key={o.id} option={o} lang={lang} selected={selected === o.id}
            onClick={() => { timer.select(o.id); setSelected(o.id); }} />
        ))}
      </div>
      <div className="row" style={{ marginTop: "1rem" }}>
        <span className="spacer" />
        <button type="button" className="btn big" disabled={!selected}
          onClick={() => { if (selected && !sent.current) { sent.current = true; onAnswer(selected, timer); } }}>
          {t(lang, "next")}
        </button>
      </div>
    </div>
  );
}
