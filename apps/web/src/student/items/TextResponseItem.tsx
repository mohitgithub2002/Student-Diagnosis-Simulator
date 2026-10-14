import { useEffect, useRef, useState } from "react";
import {
  answerFromText, answerFromVad, readAloudFromVad, readAloudFromWords, t, type FeatureRow, type TextResponseContent,
} from "@sds/task-library";
import { Speaker } from "../../components/ui";
import { VoiceCapture } from "../../voice/capture";
import { Countdown, useItemTimer, type ItemProps } from "./common";

type Mode = "choose" | "voice" | "typed" | "silent";

/**
 * Read Aloud (T7), Explain It (T11), Guided Conversation (T22). Voice is processed on the device; the
 * typed or transcribed text is turned into numbers here and never sent anywhere.
 */
export function TextResponseItem({ item, lang, onSubmit, onIdle, voiceAllowed, onFeatures }: ItemProps) {
  const c = item.content as TextResponseContent;
  const readAloud = c.mode === "read_aloud";
  const timer = useItemTimer(item.id, onIdle);
  const canVoice = Boolean(voiceAllowed) && VoiceCapture.supported();
  const [mode, setMode] = useState<Mode>(canVoice ? (readAloud ? "voice" : "choose") : readAloud ? "silent" : "typed");
  const [recording, setRecording] = useState(false);
  const [level, setLevel] = useState(0);
  const [text, setText] = useState("");
  const [error, setError] = useState<string | null>(null);
  const capture = useRef<VoiceCapture | null>(null);
  const startedAt = useRef(0);
  const done = useRef(false);
  const prefix = c.mode === "explain" ? "t11" : "t22";

  useEffect(() => () => capture.current?.cancel(), []);

  const emit = (rows: { name: string; value: number; channel: FeatureRow["channel"] }[]) => {
    if (rows.length) onFeatures?.(rows.map((r) => ({ ...r, task_id: item.task_id, item_id: item.id })));
  };

  const finish = (extra: Record<string, unknown>, skipped = false) => {
    if (done.current) return;
    done.current = true;
    onSubmit({ item, answer: null, timer, skipped, extra });
  };

  const startVoice = async () => {
    setError(null);
    timer.activity();
    try {
      const cap = new VoiceCapture();
      cap.onLevel = (l) => setLevel(l);
      await cap.start(lang);
      capture.current = cap;
      startedAt.current = performance.now();
      setRecording(true);
    } catch {
      setError(t(lang, "mic_unavailable"));
      setMode(readAloud ? "silent" : "typed");
    }
  };

  const stopVoice = async () => {
    const cap = capture.current;
    if (!cap) return;
    timer.activity();
    setRecording(false);
    const res = await cap.stop();
    capture.current = null;
    if (readAloud) {
      emit(res.words?.length ? readAloudFromWords(c.passage ?? "", res.words) : readAloudFromVad(c.word_count ?? 0, res.vad));
    } else if (res.transcript) {
      emit(answerFromText(prefix, res.transcript, "voice", c.keywords, {
        speech_start_ms: res.vad.speech_start_ms ?? undefined, pauses: res.vad.pause_count,
      }));
    } else {
      emit(answerFromVad(prefix, res.vad));
    }
    finish({ mode: "voice", stt: Boolean(res.words?.length) }, !readAloud && res.vad.speech_start_ms === null);
  };

  const submitTyped = () => {
    emit(answerFromText(prefix, text, "text", c.keywords));
    setText(""); // the words themselves are discarded
    finish({ mode: "typed" }, text.trim().length === 0);
  };

  const prompt = readAloud ? t(lang, "i_read_it") : c.prompt ?? "";
  return (
    <div className="stack">
      {readAloud ? (
        <div className="passage"><h3>{c.title}</h3><p>{c.passage}</p></div>
      ) : (
        <div className="row" style={{ alignItems: "flex-start" }}>
          <p className="prompt" style={{ flex: 1, margin: 0 }}>{c.prompt}</p>
          <Speaker text={prompt} lang={lang} />
        </div>
      )}
      {error && <div className="alert error">{error}</div>}

      {mode === "choose" && (
        <div className="row">
          <button type="button" className="btn big" onClick={() => { setMode("voice"); }}>{t(lang, "speak")}</button>
          <button type="button" className="btn big secondary" onClick={() => setMode("typed")}>{t(lang, "type_instead")}</button>
          <span className="spacer" />
          {c.mode === "converse" && <button type="button" className="btn ghost" onClick={() => finish({ mode: "skipped" }, true)}>{t(lang, "skip")}</button>}
        </div>
      )}

      {mode === "voice" && (
        <div className="stack">
          <p className="small muted">{t(lang, "voice_note")}</p>
          <div className="bar" aria-hidden="true"><span style={{ width: `${Math.min(100, level * 400)}%` }} /></div>
          <div className="row">
            {!recording ? (
              <button type="button" className="btn big" onClick={startVoice}>{t(lang, "start_speaking")}</button>
            ) : (
              <>
                <span className="badge warn">{t(lang, "listening")}</span>
                {!readAloud && <Countdown seconds={c.time_limit_s} onEnd={stopVoice} label={(s) => t(lang, "seconds_left", { s })} />}
                <span className="spacer" />
                <button type="button" className="btn big" onClick={stopVoice}>{t(lang, readAloud ? "done" : "stop")}</button>
              </>
            )}
            {!recording && !readAloud && (
              <button type="button" className="btn secondary" onClick={() => setMode("typed")}>{t(lang, "type_instead")}</button>
            )}
          </div>
        </div>
      )}

      {mode === "typed" && (
        <div className="stack">
          <textarea value={text} onChange={(e) => { timer.activity(); setText(e.target.value); }}
            placeholder={t(lang, "type_here")} aria-label={t(lang, "type_here")} autoFocus />
          <div className="row">
            <Countdown seconds={c.time_limit_s + 60} onEnd={submitTyped} label={(s) => t(lang, "seconds_left", { s })} />
            <span className="spacer" />
            {c.mode === "converse" && <button type="button" className="btn ghost" onClick={() => finish({ mode: "skipped" }, true)}>{t(lang, "skip")}</button>}
            <button type="button" className="btn big" onClick={submitTyped}>{t(lang, "done")}</button>
          </div>
        </div>
      )}

      {mode === "silent" && (
        <div className="row">
          <span className="spacer" />
          <button type="button" className="btn big" onClick={() => finish({ mode: "silent" })}>{t(lang, "i_read_it")}</button>
        </div>
      )}
    </div>
  );
}
