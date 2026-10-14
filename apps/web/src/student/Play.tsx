import { useCallback, useEffect, useMemo, useRef, useState, useSyncExternalStore } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { OfflineBuffer, SessionRunner, t, type Bundle, type FeatureRow, type Lang } from "@sds/task-library";
import { client, errorText, getAuth } from "../api";
import { Alert, Speaker } from "../components/ui";
import { deviceStorage } from "../storage";
import { ItemRenderer } from "./ItemRenderer";
import type { SubmitFn } from "./items/common";

function useRunner(runner: SessionRunner | null) {
  const subscribe = useCallback((fn: () => void) => (runner ? runner.subscribe(fn) : () => undefined), [runner]);
  const [, force] = useState(0);
  useSyncExternalStore(subscribe, () => (runner ? `${runner.step.kind}:${runner.state.seq}:${runner.pauseOffered}:${Boolean(runner.pendingConfidence)}` : ""));
  return force;
}

export function Play() {
  const { number } = useParams();
  const n = Number(number);
  const navigate = useNavigate();
  const auth = getAuth("student");
  const api = useMemo(() => client(auth?.token), [auth?.token]);
  const buffer = useMemo(() => new OfflineBuffer(deviceStorage(), `sds.queue.${auth?.student?.id ?? "anon"}`), [auth?.student?.id]);
  const [runner, setRunner] = useState<SessionRunner | null>(null);
  const [bundle, setBundle] = useState<Bundle | null>(null);
  const [voiceAllowed, setVoiceAllowed] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(0);
  const [online, setOnline] = useState(navigator.onLine);
  const lastTask = useRef(-1);
  useRunner(runner);

  const lang = (bundle?.language ?? auth?.student?.language ?? "en") as Lang;
  // Answers are written to the device first; syncing is batched a couple of seconds behind.
  const flushTimer = useRef<number | null>(null);
  const scheduleFlush = useCallback(() => {
    if (flushTimer.current !== null) return;
    flushTimer.current = window.setTimeout(() => {
      flushTimer.current = null;
      void buffer.flush(api);
    }, 2000);
  }, [buffer, api]);

  useEffect(() => {
    if (!auth) {
      navigate("/play");
      return;
    }
    let alive = true;
    api.startSession(n, "web").then(
      (res) => {
        if (!alive) return;
        setBundle(res.bundle);
        setVoiceAllowed(res.voice_allowed);
        const r = new SessionRunner(res.bundle, {
          onEvent: (ev) => {
            void buffer.push({ type: "events", session: n, events: [ev] }).then(scheduleFlush);
          },
          uuid: () => crypto.randomUUID(),
          startTask: res.resume_state?.completedTasks ?? 0,
          seq: res.resume_state?.seq ?? 0,
        });
        setRunner(r);
      },
      (e) => alive && setError(errorText(e)),
    );
    return () => {
      alive = false;
    };
  }, [n]); // eslint-disable-line react-hooks/exhaustive-deps

  // Keep the queue moving: retry every 10 s and as soon as the connection returns.
  useEffect(() => {
    const off = buffer.onChange(setPending);
    void buffer.pending().then(setPending);
    const tryFlush = () => void buffer.flush(api);
    const id = window.setInterval(tryFlush, 10000);
    const up = () => { setOnline(true); tryFlush(); };
    const down = () => setOnline(false);
    window.addEventListener("online", up);
    window.addEventListener("offline", down);
    return () => {
      off();
      window.clearInterval(id);
      window.removeEventListener("online", up);
      window.removeEventListener("offline", down);
    };
  }, [buffer, api]);

  // Save resume state whenever a task finishes, and complete the session at the end.
  useEffect(() => {
    if (!runner) return;
    const s = runner.state;
    if (s.completedTasks !== lastTask.current) {
      lastTask.current = s.completedTasks;
      if (runner.step.kind === "session_done") {
        void buffer.push({ type: "complete", session: n }).then(() => buffer.flush(api));
      } else if (s.completedTasks > 0) {
        void buffer.push({ type: "state", session: n, state: { ...s } }).then(() => buffer.flush(api));
      }
    }
  });

  const onSubmit: SubmitFn = useCallback(({ timer, ...rest }) => {
    runner?.submit({ ...rest, timing: timer.finish(), shownAtEpoch: timer.shownAtEpoch });
  }, [runner]);
  const onFeatures = useCallback((rows: FeatureRow[]) => {
    void buffer.push({ type: "features", session: n, features: rows }).then(() => buffer.flush(api));
  }, [buffer, api, n]);
  const onIdle = useCallback((ms: number) => runner?.idle(ms), [runner]);

  if (error) {
    return (
      <div className="page narrow stack">
        <Alert kind="error">{error}</Alert>
        <button type="button" className="btn" onClick={() => navigate("/play/home")}>{t(lang, "back")}</button>
      </div>
    );
  }
  if (!runner || !bundle) return <div className="page narrow"><p className="muted">{t(lang, "loading")}</p></div>;

  const step = runner.step;
  const progress = runner.progress;
  return (
    <div className="page">
      <div className="game-header">
        <span className="title">{t(lang, "level", { n })}</span>
        <div className="progress-dots" aria-label={t(lang, "of", { a: progress.taskIndex + 1, b: progress.tasks })}>
          {bundle.tasks.map((_, i) => (
            <span key={i} className={i < progress.taskIndex ? "done" : i === progress.taskIndex ? "now" : ""} />
          ))}
        </div>
        <span className="spacer" />
        {(!online || pending > 0) && (
          <span className={`badge ${online ? "" : "warn"}`} title={t(lang, "offline")}>
            {online ? t(lang, "syncing") : t(lang, "offline")}
          </span>
        )}
      </div>

      <div className="stage">
        {step.kind === "task_intro" && (
          <div className="stack center" style={{ paddingTop: "2rem" }}>
            <p className="muted">{t(lang, "task_intro")}</p>
            <h1>{step.entry.title}</h1>
            <div className="row" style={{ justifyContent: "center" }}>
              <p className="prompt" style={{ maxWidth: 560, fontWeight: 500 }}>{step.entry.instructions}</p>
              <Speaker text={step.entry.instructions} lang={lang} />
            </div>
            <button type="button" className="btn big" onClick={() => runner.begin()}>{t(lang, "lets_go")}</button>
          </div>
        )}
        {step.kind === "present" && (
          <div>
            {step.presentation.entry.task_id === "T17" && (
              <p className="badge" style={{ marginBottom: "0.5rem" }}>
                {t(lang, step.presentation.condition === "pressure" ? "t17.pressure" : "t17.relaxed")}
              </p>
            )}
            <ItemRenderer key={step.presentation.key} p={step.presentation} lang={lang} aux={bundle.aux_items}
              voiceAllowed={voiceAllowed} onSubmit={onSubmit} onIdle={onIdle} onFeatures={onFeatures} />
          </div>
        )}
        {step.kind === "session_done" && (
          <div className="stack center" style={{ paddingTop: "3rem" }}>
            <div style={{ fontSize: "4rem" }} aria-hidden="true">
              <span className="star">★</span><span className="star">★</span><span className="star">★</span>
            </div>
            <h1>{t(lang, "session_complete")}</h1>
            <p>{t(lang, "session_complete_text")}</p>
            {pending > 0 && <p className="small muted">{online ? t(lang, "syncing") : t(lang, "offline")}</p>}
            <button type="button" className="btn big" onClick={() => navigate("/play/home")}>{t(lang, "continue")}</button>
          </div>
        )}
      </div>

      {runner.pendingConfidence && <ConfidenceSheet lang={lang} onRate={(c) => runner.rate(c)} />}
      {runner.pauseOffered && step.kind === "present" && !runner.pendingConfidence && (
        <div className="overlay" role="dialog" aria-modal="true" aria-labelledby="pause-title">
          <div className="sheet stack center">
            <h2 id="pause-title">{t(lang, "pause_title")}</h2>
            <p>{t(lang, "pause_text")}</p>
            <div className="row" style={{ justifyContent: "center" }}>
              <button type="button" className="btn big secondary" onClick={() => {
                void buffer.push({ type: "state", session: n, state: { ...runner.state } }).then(() => buffer.flush(api));
                navigate("/play/home");
              }}>{t(lang, "take_break")}</button>
              <button type="button" className="btn big" onClick={() => runner.dismissPause()}>{t(lang, "keep_going")}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/** T13 Confidence Rating after each scored item. */
function ConfidenceSheet({ lang, onRate }: { lang: Lang; onRate: (c: number) => void }) {
  return (
    <div className="overlay" role="dialog" aria-modal="true" aria-labelledby="conf-title">
      <div className="sheet stack">
        <h2 id="conf-title" className="center">{t(lang, "how_sure")}</h2>
        <div className="conf">
          {[1, 2, 3, 4].map((c) => (
            <button key={c} type="button" onClick={() => onRate(c)}>
              <span className="meter" aria-hidden="true">
                {[1, 2, 3, 4].map((k) => <i key={k} className={k <= c ? "on" : ""} style={{ height: 6 + k * 5 }} />)}
              </span>
              <span>{t(lang, `conf_${c}`)}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
