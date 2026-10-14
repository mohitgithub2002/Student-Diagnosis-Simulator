import { useEffect, useMemo, useRef, useState } from "react";
import { AppState, Pressable, Text, TextInput, View } from "react-native";
import {
  ItemTimer, TOKEN_COLORS, checkAnswer, dotLayout, fallbackTextMode, initialTextMode, streamSequence, t, typedOutcome,
  voiceOutcome, type AllocateContent, type BundleItem, type ChoiceContent, type Draft, type EstimateContent,
  type FeatureRow, type ItemOutcome, type Lang, type PassageQuestionsContent, type PlanRouteContent, type Presentation,
  type SequenceContent, type StreamContent, type SurveyContent, type TextMode, type TextResponseContent,
} from "@sds/task-library";
import Svg, { Circle } from "react-native-svg";
import { SdsVoice } from "../../modules/sds-voice";
import { speak } from "../platform";
import { Btn, C, Countdown, FigureView, LevelBar, Opt, P, s } from "../ui";
import { NativeVoiceCapture } from "../voice/capture";
import { installedModel } from "../voice/models";

export type Submit = (d: Omit<Draft, "timing" | "shownAtEpoch"> & { timer: ItemTimer }) => void;

interface Props {
  item: BundleItem;
  taskId: string;
  lang: Lang;
  settings: Record<string, any>;
  onSubmit: Submit;
  onIdle: (ms: number) => void;
  aux: Record<string, BundleItem>;
  onFeatures: (rows: FeatureRow[]) => void;
  voiceAllowed?: boolean;
  previous?: { answer: unknown };
  index: number;
}

/** Timer per item: counts app switches (AppState) and idle gaps on the device clock. */
function useTimer(key: string, onIdle?: (ms: number) => void): ItemTimer {
  const timer = useMemo(() => new ItemTimer(() => performance.now(), Date.now()), [key]); // eslint-disable-line
  useEffect(() => {
    const sub = AppState.addEventListener("change", (st) => timer.visibility(st !== "active"));
    const id = setInterval(() => onIdle?.(timer.idleNow()), 5000);
    return () => {
      sub.remove();
      clearInterval(id);
    };
  }, [timer]); // eslint-disable-line
  return timer;
}

function Prompt({ text, lang }: { text: string; lang: Lang }) {
  if (!text) return null;
  return (
    <Pressable onPress={() => speak(text, lang)} accessibilityHint="Tap to hear it">
      <P big>{text} 🔊</P>
    </Pressable>
  );
}

const promptOf = (lang: Lang, c: { prompt?: string; prompt_key?: string }, vars = {}) =>
  c.prompt ?? (c.prompt_key ? t(lang, c.prompt_key, vars) : "");

export function ItemView({ p, lang, aux, onSubmit, onIdle, onFeatures, voiceAllowed }: { p: Presentation; lang: Lang;
  aux: Record<string, BundleItem>; onSubmit: Submit; onIdle: (ms: number) => void; onFeatures: (rows: FeatureRow[]) => void;
  voiceAllowed?: boolean }) {
  const props: Props = {
    item: p.item, taskId: p.entry.task_id, lang, settings: p.settings, onSubmit, onIdle, aux, onFeatures, voiceAllowed,
    previous: p.previous ? { answer: p.previous.answer } : undefined, index: p.index,
  };
  switch (p.item.content.kind) {
    case "sequence": return <SequenceView {...props} />;
    case "choice": return <ChoiceView {...props} />;
    case "estimate": return <EstimateView {...props} />;
    case "stream": return <StreamView {...props} />;
    case "passage_questions": return <PassageView {...props} />;
    case "text_response": return <TextView {...props} />;
    case "plan_route": return <RouteView {...props} />;
    case "allocate": return <AllocateView {...props} />;
    case "choice_menu":
    case "bonus_offer": return <MenuView {...props} />;
    case "survey": return <SurveyView {...props} />;
    default: return <P>Unsupported item</P>;
  }
}

function ChoiceView({ item, lang, taskId, settings, onSubmit, onIdle, previous }: Props) {
  const c = item.content as ChoiceContent;
  const timer = useTimer(item.id, onIdle);
  const [sel, setSel] = useState<string | null>(previous ? String(previous.answer ?? "") || null : null);
  const [attempts, setAttempts] = useState(1);
  const [note, setNote] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<{ variant: string; first: string } | null>(null);
  const [hidden, setHidden] = useState(false);
  const done = useRef(false);
  const immediate = c.layout === "pair" && !previous;
  useEffect(() => {
    if (previous?.answer != null) timer.select(String(previous.answer));
    if (c.show_ms) {
      const id = setTimeout(() => setHidden(true), c.show_ms);
      return () => clearTimeout(id);
    }
  }, []); // eslint-disable-line
  useEffect(() => {
    if (!settings.pressure) return;
    const id = setTimeout(() => finish(null, { timeout: true }, true), (settings.pressure_seconds ?? 12) * 1000);
    return () => clearTimeout(id);
  }, []); // eslint-disable-line
  const finish = (answer: string | null, extra: Record<string, unknown> = {}, skipped = false, retries = 0) => {
    if (done.current) return;
    done.current = true;
    onSubmit({ item, answer, timer, extra, skipped, retries, askConfidence: previous ? false : undefined });
  };
  const choose = (id: string) => {
    timer.select(id);
    setSel(id);
    setNote(null);
    if (immediate && !feedback) finish(id);
  };
  const next = () => {
    if (!sel) return;
    const ok = checkAnswer(item, sel);
    if (taskId === "T19") {
      if (ok) finish(sel, { attempts, gave_up: false });
      else { setAttempts((a) => a + 1); setNote(t(lang, "t19.not_yet")); }
      return;
    }
    if (taskId === "T20") {
      if (feedback) finish(feedback.first, { retry_offered: true, feedback_variant: feedback.variant, retried: true, retry_correct: ok === true }, false, 1);
      else if (ok === false) {
        const variants = settings.feedback_variants ?? ["effort", "ability", "neutral"];
        setFeedback({ variant: variants[item.id.length % variants.length], first: sel });
        setSel(null);
      } else finish(sel);
      return;
    }
    finish(sel);
  };
  const stem = (c.stem ?? {}) as Record<string, any>;
  return (
    <View style={{ gap: 12 }}>
      {previous && <P muted>{t(lang, "review.text")}</P>}
      <Prompt text={promptOf(lang, c)} lang={lang} />
      {stem.rules && (
        <View style={s.passage}>
          {(stem.rules as string[]).map((r, i) => <P key={i}>{i + 1}. {r}</P>)}
          <P><Text style={{ fontWeight: "800" }}>{stem.fact}</Text></P>
        </View>
      )}
      {stem.figures && (
        <View style={[s.row, { justifyContent: "center" }]}>
          {(stem.figures as any[]).map((f, i) => <FigureView key={i} figure={f} size={70} />)}
          {stem.blank && <Text style={{ fontSize: 40, color: C.muted }}>?</Text>}
        </View>
      )}
      {stem.left && stem.right && (
        <View style={[s.row, { justifyContent: "space-around" }]}>
          {[stem.left, stem.right].map((side: any, i: number) => (
            <View key={i} style={[s.card, { flex: 1, minHeight: 140, alignItems: "center", justifyContent: "center" }]}>
              {side.figure && <FigureView figure={side.figure} size={96} />}
              {side.text && <Text style={{ fontSize: 26, fontWeight: "800", letterSpacing: 4 }}>{side.text}</Text>}
              {side.prices && (side.prices as number[]).map((pr, k) => <Text key={k} style={{ fontSize: 20, fontWeight: "700" }}>₹{pr}</Text>)}
              {side.dots !== undefined && !hidden && (
                <Svg width={130} height={130} viewBox="0 0 100 100">
                  {dotLayout(side.dots, side.seed).map((d, k) => <Circle key={k} cx={d.x * 100} cy={d.y * 100} r={3.6} fill={C.ink} />)}
                </Svg>
              )}
            </View>
          ))}
        </View>
      )}
      {stem.sentence && <View style={s.passage}><P>{stem.sentence}</P><P><Text style={{ fontWeight: "800", textDecorationLine: "underline" }}>{stem.word}</Text></P></View>}
      {stem.steps && (
        <View style={s.passage}>
          <P><Text style={{ fontWeight: "800" }}>{stem.setup}</Text></P>
          {(stem.steps as string[]).map((x, i) => <P key={i}>{i + 1}. {x}</P>)}
        </View>
      )}
      {stem.equations && (
        <View style={s.passage}>
          {(stem.equations as any[]).map((eq, i) => (
            <View key={i} style={s.row}>
              {eq.terms.map((term: string, j: number) => <FigureView key={j} figure={{ shape: term, rotation: 0, count: 1, fill: "solid" }} size={34} />)}
              <Text style={{ fontSize: 22 }}>= {eq.total}</Text>
            </View>
          ))}
          <View style={s.row}><FigureView figure={{ shape: stem.ask, rotation: 0, count: 1, fill: "solid" }} size={34} /><Text style={{ fontSize: 22 }}>= ?</Text></View>
        </View>
      )}
      {feedback && <P big>{t(lang, `t20.${feedback.variant}`)} {t(lang, "t20.retry")}</P>}
      {note && <P big>{note}</P>}
      <View style={{ gap: 10, flexDirection: c.layout === "grid" || c.layout === "pair" ? "row" : "column", flexWrap: "wrap" }}>
        {c.options.map((o) => (
          <View key={o.id} style={c.layout === "grid" || c.layout === "pair" ? { width: "47%" } : undefined}>
            <Opt label={o.text ?? (o.label_key ? t(lang, o.label_key) : o.id)} selected={sel === o.id} onPress={() => choose(o.id)}>
              {o.figure ? <FigureView figure={o.figure} size={72} /> : undefined}
            </Opt>
          </View>
        ))}
      </View>
      {!immediate && (
        <View style={s.row}>
          {taskId === "T19" && <Btn kind="secondary" title={t(lang, "t19.move_on")} onPress={() => finish(sel, { attempts, gave_up: true })} />}
          {feedback && <Btn kind="secondary" title={t(lang, "next")} onPress={() => finish(feedback.first, { retry_offered: true, feedback_variant: feedback.variant, retried: false })} />}
          <Btn big title={t(lang, feedback ? "submit" : "next")} disabled={!sel} onPress={next} />
        </View>
      )}
    </View>
  );
}

function SequenceView({ item, lang, onSubmit, onIdle }: Props) {
  const c = item.content as SequenceContent;
  const [shown, setShown] = useState(-1);
  const [answer, setAnswer] = useState<string[]>([]);
  const timer = useTimer(`${item.id}:${shown >= c.sequence.length * 2}`, onIdle);
  useEffect(() => {
    let i = -1;
    let id: ReturnType<typeof setTimeout>;
    const step = () => {
      i += 1;
      setShown(i * 2);
      if (i < c.sequence.length) id = setTimeout(() => { setShown(i * 2 + 1); id = setTimeout(step, c.gap_ms); }, c.show_ms);
    };
    id = setTimeout(step, 900);
    return () => clearTimeout(id);
  }, [c]);
  const token = (tok: string, size: number) =>
    c.mode === "digits" ? <Text style={{ fontSize: size * 0.6, fontWeight: "800", color: C.brand }}>{tok}</Text>
      : c.mode === "colors" ? (
        <View style={{ alignItems: "center" }}>
          <Svg width={size * 0.7} height={size * 0.7} viewBox="0 0 40 40"><Circle cx="20" cy="20" r="17" fill={TOKEN_COLORS[tok]} /></Svg>
          <Text style={{ fontSize: 11 }}>{tok}</Text>
        </View>
      ) : <FigureView figure={{ shape: tok, rotation: 0, count: 1, fill: "solid" }} size={size * 0.7} />;
  if (shown < c.sequence.length * 2) {
    const visible = shown >= 0 && shown % 2 === 0 ? c.sequence[shown / 2] : null;
    return (
      <View style={{ alignItems: "center", gap: 20 }}>
        <P big>{t(lang, "t1.watch")}</P>
        <View style={[s.card, { width: 150, height: 150, alignItems: "center", justifyContent: "center" }]}>{visible && token(visible, 140)}</View>
      </View>
    );
  }
  return (
    <View style={{ gap: 12 }}>
      <Prompt text={t(lang, c.direction === "backward" ? "t1.backward" : "t1.forward")} lang={lang} />
      <View style={[s.row, { minHeight: 56, backgroundColor: "#f7f9fc", borderRadius: 12, padding: 6 }]}>{answer.map((tok, i) => <View key={i}>{token(tok, 48)}</View>)}</View>
      <View style={[s.row, { justifyContent: "center" }]}>
        {c.choices.map((tok) => (
          <Pressable key={tok} accessibilityLabel={tok} onPress={() => { timer.activity(); setAnswer((a) => (a.length < c.sequence.length ? [...a, tok] : a)); }}
            style={[s.opt, { width: 72, height: 72 }]}>{token(tok, 64)}</Pressable>
        ))}
      </View>
      <View style={s.row}>
        <Btn kind="secondary" title={t(lang, "undo")} disabled={!answer.length} onPress={() => setAnswer((a) => a.slice(0, -1))} />
        <Btn big title={t(lang, "next")} disabled={answer.length !== c.sequence.length} onPress={() => onSubmit({ item, answer, timer })} />
      </View>
    </View>
  );
}

function EstimateView({ item, lang, onSubmit, onIdle }: Props) {
  const c = item.content as EstimateContent;
  const timer = useTimer(item.id, onIdle);
  const [value, setValue] = useState<number | null>(null);
  const [width, setWidth] = useState(1);
  return (
    <View style={{ gap: 16 }}>
      <Prompt text={t(lang, c.prompt_key, { target: c.target })} lang={lang} />
      <Pressable onLayout={(e) => setWidth(e.nativeEvent.layout.width)} accessibilityRole="adjustable"
        onPress={(e) => {
          const frac = Math.min(1, Math.max(0, e.nativeEvent.locationX / width));
          const v = Math.round((c.min + frac * (c.max - c.min)) / c.step) * c.step;
          timer.select(v);
          setValue(v);
        }} style={{ height: 70, justifyContent: "center" }}>
        <View style={{ height: 6, backgroundColor: C.brand, borderRadius: 3 }} />
        {value !== null && <View style={{ position: "absolute", left: ((value - c.min) / (c.max - c.min)) * width - 10, top: 10, width: 20, height: 50, backgroundColor: "#e07a1f", borderRadius: 10 }} />}
      </Pressable>
      <View style={[s.row, { justifyContent: "space-between" }]}><P>{c.min}</P><P>{c.max}</P></View>
      <Btn big title={t(lang, "next")} disabled={value === null} onPress={() => onSubmit({ item, answer: value, timer })} />
    </View>
  );
}

function StreamView({ item, lang, onSubmit, index }: Props) {
  const c = item.content as StreamContent;
  const stimuli = useMemo(() => streamSequence(c), [c]);
  const timer = useTimer(item.id);
  const [running, setRunning] = useState(index > 1);
  const [cur, setCur] = useState<{ i: number; on: boolean }>({ i: -1, on: false });
  const taps = useRef<{ i: number; rt: number }[]>([]);
  const onset = useRef(0);
  const curRef = useRef(-1);
  useEffect(() => {
    if (!running) return;
    let i = -1;
    const timers: ReturnType<typeof setTimeout>[] = [];
    const tick = () => {
      i += 1;
      if (i >= stimuli.length) { onSubmit({ item, answer: { taps: taps.current }, timer, extra: { block: index } }); return; }
      curRef.current = i;
      onset.current = performance.now();
      setCur({ i, on: true });
      timers.push(setTimeout(() => setCur({ i, on: false }), c.stim_ms));
      timers.push(setTimeout(tick, c.isi_ms));
    };
    timers.push(setTimeout(tick, 600));
    return () => timers.forEach(clearTimeout);
  }, [running]); // eslint-disable-line
  if (!running) {
    return (
      <View style={{ alignItems: "center", gap: 16 }}>
        <P big>{t(lang, c.prompt_key)}</P>
        <FigureView figure={c.target} size={130} />
        <Btn big title={t(lang, "start")} onPress={() => setRunning(true)} />
      </View>
    );
  }
  return (
    <View style={{ gap: 16 }}>
      <View style={[s.card, { height: 240, alignItems: "center", justifyContent: "center" }]}>
        {cur.on && cur.i >= 0 && <FigureView figure={stimuli[cur.i].figure} size={160} />}
      </View>
      <Pressable onPressIn={() => {
        const i = curRef.current;
        if (i >= 0 && !taps.current.some((x) => x.i === i)) { timer.activity(); taps.current.push({ i, rt: Math.round(performance.now() - onset.current) }); }
      }} style={{ height: 120, borderRadius: 22, backgroundColor: C.brand2, alignItems: "center", justifyContent: "center" }}>
        <Text style={{ color: "#fff", fontSize: 28, fontWeight: "800" }}>{t(lang, "t3.tap_here")}</Text>
      </Pressable>
    </View>
  );
}

function PassageView({ item, lang, settings, onSubmit, onIdle, aux }: Props) {
  const c = item.content as PassageQuestionsContent;
  const setA = c.questions.filter((q) => (q.set ?? "A") === "A");
  const setB = c.questions.filter((q) => q.set === "B");
  const order = c.mode === "lesson" ? [...setA, ...setB] : c.questions;
  const distractors: string[] = (settings.distractor_ids ?? []).filter((id: string) => id in aux);
  const [phase, setPhase] = useState<{ k: "study" | "recap" | "distractor" | "q"; i: number }>(
    settings.phase === "delayed" ? { k: "q", i: 0 } : { k: "study", i: 0 });
  const [rereads, setRereads] = useState(0);
  const [peek, setPeek] = useState(false);
  const studyTimer = useRef(new ItemTimer(() => performance.now(), Date.now()));
  const [sel, setSel] = useState<string | null>(null);
  const qTimer = useRef(new ItemTimer(() => performance.now(), Date.now()));
  useEffect(() => { onIdle(0); }, []); // eslint-disable-line

  if (phase.k === "study" || phase.k === "recap") {
    const recap = phase.k === "recap";
    const text = recap ? c.recap?.text : c.card ? `${c.card.title}\n\n${c.card.lines.join("\n")}` : c.lesson ? `${c.lesson.title}\n\n${c.lesson.sections.join("\n\n")}` : `${c.passage?.title}\n\n${c.passage?.text}`;
    return (
      <View style={{ gap: 12 }}>
        <P big>{t(lang, recap ? "lesson.recap" : c.mode === "card" ? "card.study" : c.mode === "lesson" ? "lesson.learn" : "passage.read")}</P>
        <View style={s.passage}><P>{text}</P></View>
        <Btn big title={t(lang, c.mode === "passage" ? "done_reading" : "ready")} onPress={() => {
          onSubmit({ item, answer: null, timer: studyTimer.current, final: false, askConfidence: false, extra: { phase: recap ? "recap" : "study" } });
          studyTimer.current = new ItemTimer(() => performance.now(), Date.now());
          qTimer.current = new ItemTimer(() => performance.now(), Date.now());
          setPhase(recap ? { k: "q", i: setA.length } : distractors.length && c.mode === "card" ? { k: "distractor", i: 0 } : { k: "q", i: 0 });
        }} />
      </View>
    );
  }
  if (phase.k === "distractor") {
    const sub = aux[distractors[phase.i]];
    return (
      <ChoiceView key={sub.id} item={sub} taskId="T4" lang={lang} settings={{}} onIdle={onIdle} aux={aux} onFeatures={() => undefined} index={0}
        onSubmit={(d) => {
          onSubmit({ ...d, condition: "t2_distractor", final: false, askConfidence: false });
          qTimer.current = new ItemTimer(() => performance.now(), Date.now());
          setPhase(phase.i + 1 < distractors.length ? { k: "distractor", i: phase.i + 1 } : { k: "q", i: 0 });
        }} />
    );
  }
  const q = order[phase.i];
  return (
    <View style={{ gap: 12 }}>
      {c.mode === "passage" && <Btn kind="secondary" title={t(lang, "read_again")} onPress={() => { if (!peek) setRereads((r) => r + 1); setPeek(!peek); }} />}
      {peek && <View style={s.passage}><P>{c.passage?.text}</P></View>}
      <Prompt text={q.prompt} lang={lang} />
      {q.options.map((o) => <Opt key={o.id} label={o.text} selected={sel === o.id} onPress={() => { qTimer.current.select(o.id); setSel(o.id); }} />)}
      <Btn big title={t(lang, "next")} disabled={!sel} onPress={() => {
        const last = phase.i === order.length - 1;
        onSubmit({ item, answer: sel, timer: qTimer.current, final: last, extra: { qid: q.id, qtype: q.qtype, set: q.set, rereads } });
        setSel(null);
        setPeek(false);
        setRereads(0);
        qTimer.current = new ItemTimer(() => performance.now(), Date.now());
        if (!last) setPhase(c.mode === "lesson" && phase.i + 1 === setA.length && c.recap ? { k: "recap", i: 0 } : { k: "q", i: phase.i + 1 });
      }} />
    </View>
  );
}

/**
 * Read Aloud (T7), Explain It (T11), Guided Conversation (T22). With the parent's voice consent the answer
 * can be spoken: the native module keeps audio in memory and hands back only numbers and recognised words,
 * which become features here with the same shared code as the web. Otherwise (no consent, Expo Go, mic
 * refused) the student reads silently or types.
 */
function TextView({ item, lang, onSubmit, onIdle, onFeatures, voiceAllowed }: Props) {
  const c = item.content as TextResponseContent;
  const readAloud = c.mode === "read_aloud";
  const timer = useTimer(item.id, onIdle);
  const canVoice = Boolean(voiceAllowed) && NativeVoiceCapture.supported();
  const [mode, setMode] = useState<TextMode>(initialTextMode(c, canVoice));
  const [phase, setPhase] = useState<"idle" | "recording" | "processing">("idle");
  const [level, setLevel] = useState(0);
  const [text, setText] = useState("");
  const [error, setError] = useState<string | null>(null);
  const capture = useRef<NativeVoiceCapture | null>(null);
  const done = useRef(false);

  useEffect(() => {
    if (canVoice) {
      void installedModel(lang).then((path) => (path ? SdsVoice?.preloadModel(path) : undefined)).catch(() => undefined);
    }
    // Android silences the microphone in the background: drop the attempt and let the student start again.
    const sub = AppState.addEventListener("change", (st) => {
      if (st !== "active" && capture.current) {
        capture.current.cancel();
        capture.current = null;
        setPhase("idle");
        setLevel(0);
      }
    });
    return () => {
      sub.remove();
      capture.current?.cancel();
    };
  }, []); // eslint-disable-line

  const finish = (extra: Record<string, unknown>, skipped = false) => {
    if (done.current) return;
    done.current = true;
    onSubmit({ item, answer: null, timer, skipped, extra });
  };

  const complete = ({ features, extra, skipped }: ItemOutcome) => {
    if (features.length) onFeatures(features.map((f) => ({ ...f, task_id: item.task_id, item_id: item.id })));
    finish(extra, skipped);
  };

  const micFailed = () => {
    setError(t(lang, "mic_unavailable"));
    setMode(fallbackTextMode(c));
  };

  const startVoice = async () => {
    setError(null);
    timer.activity();
    const cap = new NativeVoiceCapture();
    cap.onLevel = setLevel;
    try {
      await cap.start(lang);
      capture.current = cap;
      setPhase("recording");
    } catch {
      micFailed();
    }
  };

  const stopVoice = async () => {
    const cap = capture.current;
    if (!cap) return;
    capture.current = null;
    timer.activity();
    setPhase("processing");
    const res = await cap.stop();
    setPhase("idle");
    setLevel(0);
    if (res.inputSilent) return micFailed(); // the microphone is switched off in Android's privacy settings
    complete(voiceOutcome(c, res));
  };

  const submitTyped = () => {
    const outcome = typedOutcome(c, text);
    setText(""); // the words themselves are discarded
    complete(outcome);
  };

  const skip = c.mode === "converse"
    ? <Btn kind="ghost" title={t(lang, "skip")} onPress={() => finish({ mode: "skipped" }, true)} />
    : null;

  return (
    <View style={{ gap: 12 }}>
      {readAloud
        ? <View style={s.passage}><P><Text style={{ fontWeight: "800" }}>{c.title}</Text>{"\n\n"}{c.passage}</P></View>
        : phase === "idle" ? <Prompt text={c.prompt ?? ""} lang={lang} /> : <P big>{c.prompt}</P>}
      {error && <Text style={{ color: C.danger }}>{error}</Text>}

      {mode === "choose" && (
        <View style={s.row}>
          <Btn big title={t(lang, "speak")} onPress={() => setMode("voice")} />
          <Btn big kind="secondary" title={t(lang, "type_instead")} onPress={() => setMode("typed")} />
          {skip}
        </View>
      )}

      {mode === "voice" && (
        <View style={{ gap: 10 }}>
          <P muted>{t(lang, "voice_note")}</P>
          <LevelBar level={level} />
          {phase === "idle" && (
            <View style={s.row}>
              <Btn big title={t(lang, "start_speaking")} onPress={startVoice} />
              {!readAloud && <Btn kind="secondary" title={t(lang, "type_instead")} onPress={() => setMode("typed")} />}
            </View>
          )}
          {phase === "recording" && (
            <View style={s.row}>
              <Text style={{ color: C.grow, fontWeight: "800" }}>{t(lang, "listening")}</Text>
              {/* Explain and converse are timed; read aloud stops itself at the time limit without a visible clock. */}
              <Countdown seconds={c.time_limit_s} onEnd={stopVoice} hidden={readAloud}
                label={(sec) => t(lang, "seconds_left", { s: sec })} />
              <Btn big title={t(lang, readAloud ? "done" : "stop")} onPress={stopVoice} />
            </View>
          )}
          {phase === "processing" && <P muted>{t(lang, "voice.processing")}</P>}
        </View>
      )}

      {mode === "typed" && (
        <View style={{ gap: 10 }}>
          <TextInput style={[s.input, { minHeight: 140, textAlignVertical: "top" }]} multiline value={text}
            onChangeText={(v) => { timer.activity(); setText(v); }} placeholder={t(lang, "type_here")} />
          <View style={s.row}>
            <Countdown seconds={c.time_limit_s + 60} onEnd={submitTyped} label={(sec) => t(lang, "seconds_left", { s: sec })} />
            {skip}
            <Btn big title={t(lang, "done")} onPress={submitTyped} />
          </View>
        </View>
      )}

      {mode === "silent" && <Btn big title={t(lang, "i_read_it")} onPress={() => finish({ mode: "silent" })} />}
    </View>
  );
}

function RouteView({ item, lang, onSubmit, onIdle }: Props) {
  const c = item.content as PlanRouteContent;
  const timer = useTimer(item.id, onIdle);
  const [route, setRoute] = useState<string[]>([]);
  const [restarts, setRestarts] = useState(0);
  const planMs = useRef<number | null>(null);
  const at = new Map(c.places.map((p) => [`${p.pos[0]},${p.pos[1]}`, p]));
  const rows = [];
  for (let y = 0; y < c.grid; y++) {
    const cells = [];
    for (let x = 0; x < c.grid; x++) {
      const place = at.get(`${x},${y}`);
      const home = c.start[0] === x && c.start[1] === y;
      const n = place ? route.indexOf(place.id) : -1;
      cells.push(
        <Pressable key={x} disabled={!place} onPress={() => {
          if (!place || route.includes(place.id)) return;
          if (planMs.current === null) planMs.current = timer.finish().response_ms;
          timer.activity();
          setRoute((r) => [...r, place.id]);
        }} style={{ flex: 1, aspectRatio: 1, margin: 2, borderRadius: 6, alignItems: "center", justifyContent: "center",
          backgroundColor: home ? C.accent : n >= 0 ? C.brand2 : place ? "#eaf2fb" : "#fff" }}>
          <Text style={{ fontSize: 9, textAlign: "center", color: n >= 0 ? "#fff" : C.ink, fontWeight: "700" }}>
            {home ? t(lang, "home") : place ? `${n >= 0 ? `${n + 1}.` : ""}${t(lang, place.label_key)}` : ""}
          </Text>
        </Pressable>,
      );
    }
    rows.push(<View key={y} style={{ flexDirection: "row" }}>{cells}</View>);
  }
  return (
    <View style={{ gap: 12 }}>
      <Prompt text={t(lang, c.prompt_key)} lang={lang} />
      <View style={{ backgroundColor: "#e8eef4", padding: 4, borderRadius: 12 }}>{rows}</View>
      <View style={s.row}>
        <Btn kind="secondary" title={t(lang, "reset")} disabled={!route.length} onPress={() => { setRestarts((r) => r + 1); setRoute([]); }} />
        <Btn big title={t(lang, "done")} disabled={route.length !== c.places.length}
          onPress={() => onSubmit({ item, answer: route, timer, extra: { plan_ms: planMs.current ?? 0, restarts } })} />
      </View>
    </View>
  );
}

function AllocateView(props: Props) {
  const { item, lang, onSubmit, aux } = props;
  const c = item.content as AllocateContent;
  const [planned, setPlanned] = useState<Record<string, number>>(Object.fromEntries(c.blocks.map((b) => [b.id, Math.round(c.total_s / c.blocks.length)])));
  const [playing, setPlaying] = useState(false);
  const [bi, setBi] = useState(0);
  const [ii, setIi] = useState(0);
  const started = useRef(0);
  const blockStart = useRef(0);
  const actual = useRef<Record<string, number>>({});
  const answered = useRef(0);
  const timer = useRef(new ItemTimer(() => performance.now(), Date.now())).current;
  const finished = useRef(false);
  const close = () => { const b = c.blocks[bi]; if (b) actual.current[b.id] = Math.round((performance.now() - blockStart.current) / 1000); };
  const end = () => {
    if (finished.current) return;
    finished.current = true;
    close();
    const total = c.blocks.reduce((a, b) => a + b.item_ids.length, 0);
    onSubmit({ item, answer: null, timer, askConfidence: false, extra: { planned, actual: actual.current, unfinished: total - answered.current,
      unused_s: Math.max(0, Math.round(c.total_s - (performance.now() - started.current) / 1000)) } });
  };
  useEffect(() => {
    if (!playing) return;
    const id = setTimeout(end, c.total_s * 1000);
    return () => clearTimeout(id);
  }, [playing]); // eslint-disable-line
  const used = Object.values(planned).reduce((a, b) => a + b, 0);
  if (!playing) {
    return (
      <View style={{ gap: 12 }}>
        <Prompt text={t(lang, c.prompt_key, { total: c.total_s })} lang={lang} />
        {c.blocks.map((b) => (
          <View key={b.id} style={s.row}>
            <P>{t(lang, b.label_key)} ({t(lang, `t16.${b.difficulty}`)}): {planned[b.id]}s</P>
            <Btn kind="secondary" title="−" onPress={() => setPlanned((p) => ({ ...p, [b.id]: Math.max(0, p[b.id] - 10) }))} />
            <Btn kind="secondary" title="+" onPress={() => setPlanned((p) => ({ ...p, [b.id]: p[b.id] + 10 }))} />
          </View>
        ))}
        <P muted>{used} / {c.total_s}</P>
        <Btn big title={t(lang, "start")} disabled={used !== c.total_s} onPress={() => { started.current = blockStart.current = performance.now(); setPlaying(true); }} />
      </View>
    );
  }
  const block = c.blocks[bi];
  const refs = block.item_ids.filter((id) => id in aux);
  const sub = aux[refs[ii]];
  const nextBlock = () => {
    close();
    if (bi + 1 >= c.blocks.length) end();
    else { blockStart.current = performance.now(); setBi(bi + 1); setIi(0); }
  };
  const subSubmit: Submit = (d) => {
    answered.current += 1;
    onSubmit({ ...d, condition: `t16:${block.id}`, final: false, askConfidence: false });
    if (ii + 1 < refs.length) setIi(ii + 1);
    else nextBlock();
  };
  return (
    <View style={{ gap: 12 }}>
      <View style={s.row}><P big>{t(lang, block.label_key)}</P><Btn kind="secondary" title={t(lang, "t16.next_pack")} onPress={nextBlock} /></View>
      {sub && (sub.content.kind === "estimate"
        ? <EstimateView key={sub.id} {...props} item={sub} onSubmit={subSubmit} />
        : <ChoiceView key={sub.id} {...props} item={sub} taskId="T16" settings={{}} onSubmit={subSubmit} />)}
    </View>
  );
}

function MenuView({ item, lang, onSubmit, onIdle }: Props) {
  const timer = useTimer(item.id, onIdle);
  const pick = (answer: string) => { timer.select(answer); onSubmit({ item, answer, timer, askConfidence: false }); };
  if (item.content.kind === "bonus_offer") {
    return (
      <View style={{ gap: 12 }}>
        <Prompt text={t(lang, item.content.prompt_key)} lang={lang} />
        <Btn big title={t(lang, "yes_please")} onPress={() => pick("accept")} />
        <Btn big kind="secondary" title={t(lang, "no_thanks")} onPress={() => pick("decline")} />
      </View>
    );
  }
  return (
    <View style={{ gap: 12 }}>
      <Prompt text={t(lang, "t18.pick")} lang={lang} />
      <Opt label={`${t(lang, "t18.familiar")} ★`} selected={false} onPress={() => pick("easy")} />
      <Opt label={`${t(lang, "t18.new")} ★★★`} selected={false} onPress={() => pick("hard")} />
    </View>
  );
}

function SurveyView({ item, lang, onSubmit, onIdle }: Props) {
  const c = item.content as SurveyContent;
  const timer = useTimer(item.id, onIdle);
  const [sel, setSel] = useState<string | null>(null);
  return (
    <View style={{ gap: 10 }}>
      <Prompt text={c.prompt} lang={lang} />
      {c.options.map((o) => <Opt key={o.id} label={o.text} selected={sel === o.id} onPress={() => { timer.select(o.id); setSel(o.id); }} />)}
      <Btn big title={t(lang, "next")} disabled={!sel} onPress={() => onSubmit({ item, answer: sel, timer })} />
    </View>
  );
}
