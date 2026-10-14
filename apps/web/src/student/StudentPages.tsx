import { useEffect, useRef, useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { LANGUAGE_NAMES, t, type Lang } from "@sds/task-library";
import { api, errorText, getAuth, setAuth } from "../api";
import { Alert, Field, Logo, formatDate, speak, useAsync } from "../components/ui";
import { VoiceCapture } from "../voice/capture";

function useLang(): Lang {
  return (getAuth("student")?.student?.language ?? "en") as Lang;
}

export function StudentLogin() {
  const navigate = useNavigate();
  const [code, setCode] = useState("");
  const [pin, setPin] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res = await api("POST", "/api/auth/student/login", { class_code: code.trim(), pin: pin.trim() });
      setAuth("student", { token: res.token, role: "student", student: res.student });
      navigate("/play/warmup");
    } catch (err) {
      const msg = errorText(err);
      setError(msg === "consent_required" ? "Your parent has not given consent yet. Please ask your teacher." : msg);
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="page narrow" style={{ paddingTop: "3rem" }}>
      <div className="card stack">
        <div className="center" style={{ color: "#17324d" }}><Logo size={56} /></div>
        <h1 className="center">{t("en", "login.title")}</h1>
        <form className="stack" onSubmit={submit}>
          <Field label={t("en", "login.class_code")}>
            <input type="text" value={code} onChange={(e) => setCode(e.target.value.toUpperCase())} autoCapitalize="characters"
              autoComplete="off" required maxLength={12} />
          </Field>
          <Field label={t("en", "login.pin")}>
            <input type="password" inputMode="numeric" pattern="\d{4}" maxLength={4} value={pin}
              onChange={(e) => setPin(e.target.value.replace(/\D/g, ""))} required />
          </Field>
          <Alert kind="error">{error}</Alert>
          <button className="btn big block" disabled={busy}>{t("en", "login.go")}</button>
        </form>
      </div>
    </div>
  );
}

export function Warmup() {
  const navigate = useNavigate();
  const auth = getAuth("student");
  const [lang, setLang] = useState<Lang>((auth?.student?.language ?? "en") as Lang);
  const [heard, setHeard] = useState(false);
  const [mic, setMic] = useState<"idle" | "listening" | "ok" | "skipped" | "unavailable">(VoiceCapture.supported() ? "idle" : "unavailable");
  const [scale, setScale] = useState(() => Number(localStorage.getItem("sds.scale") ?? "1"));
  const [error, setError] = useState<string | null>(null);
  const cap = useRef<VoiceCapture | null>(null);

  useEffect(() => {
    document.documentElement.style.setProperty("--scale", String(scale));
    try { localStorage.setItem("sds.scale", String(scale)); } catch { /* ignore */ }
  }, [scale]);
  useEffect(() => () => cap.current?.cancel(), []);

  if (!auth) {
    navigate("/play");
    return null;
  }
  const testMic = async () => {
    try {
      const c = new VoiceCapture();
      cap.current = c;
      await c.start(lang, false);
      setMic("listening");
      window.setTimeout(async () => {
        const res = await c.stop();
        cap.current = null;
        setMic(res.vad.speech_start_ms !== null ? "ok" : "idle");
      }, 3500);
    } catch {
      setMic("unavailable");
    }
  };
  const go = async () => {
    try {
      await api("POST", "/api/student/warmup", { language: lang, mic_ok: mic === "ok", audio_ok: heard }, auth.token);
      setAuth("student", { ...auth, student: { ...auth.student!, language: lang } });
      navigate("/play/home");
    } catch (e) {
      setError(errorText(e));
    }
  };
  return (
    <div className="page narrow stack">
      <h1>{t(lang, "warmup.title")}</h1>
      <div className="card stack">
        <h2>{t(lang, "warmup.language")}</h2>
        <div className="row">
          {(["en", "hi", "hinglish"] as Lang[]).map((l) => (
            <button key={l} type="button" className={`btn ${l === lang ? "" : "secondary"}`} aria-pressed={l === lang}
              onClick={() => setLang(l)}>{LANGUAGE_NAMES[l]}</button>
          ))}
        </div>
      </div>
      <div className="card stack">
        <h2>{t(lang, "warmup.audio")}</h2>
        <div className="row">
          <button type="button" className="btn secondary" onClick={() => speak(t(lang, "lets_go"), lang)}>{t(lang, "warmup.play_sound")}</button>
          <button type="button" className={`btn ${heard ? "" : "secondary"}`} aria-pressed={heard} onClick={() => setHeard(true)}>
            {t(lang, "warmup.heard")}
          </button>
        </div>
      </div>
      <div className="card stack">
        <h2>{t(lang, "warmup.mic")}</h2>
        <p className="small muted">{t(lang, "voice_note")}</p>
        {mic === "unavailable" ? <p className="muted">{t(lang, "mic_unavailable")}</p> : (
          <div className="row">
            <button type="button" className="btn secondary" disabled={mic === "listening"} onClick={testMic}>
              {mic === "listening" ? t(lang, "listening") : t(lang, "start_speaking")}
            </button>
            {mic === "ok" && <span className="badge good">{t(lang, "warmup.mic_ok")}</span>}
            <button type="button" className="btn ghost" onClick={() => setMic("skipped")}>{t(lang, "warmup.mic_skip")}</button>
          </div>
        )}
      </div>
      <div className="card row">
        <strong>{t(lang, "warmup.text_size")}</strong>
        <span className="spacer" />
        {[0.9, 1, 1.15, 1.3].map((s) => (
          <button key={s} type="button" className={`btn ${scale === s ? "" : "secondary"}`} aria-pressed={scale === s}
            onClick={() => setScale(s)} style={{ fontSize: `${s}rem` }}>A</button>
        ))}
      </div>
      <Alert kind="error">{error}</Alert>
      <button type="button" className="btn big block" onClick={go}>{t(lang, "continue")}</button>
    </div>
  );
}

export function StudentHome() {
  const navigate = useNavigate();
  const auth = getAuth("student");
  const lang = useLang();
  const { data, error } = useAsync(() => api("GET", "/api/student/home", undefined, auth?.token), [auth?.token]);
  if (!auth) {
    navigate("/play");
    return null;
  }
  return (
    <div className="page stack">
      <div className="row">
        <h1 style={{ margin: 0 }}>{t(lang, "home.hello", { name: auth.student?.name.split(" ")[0] ?? "" })}</h1>
        <span className="spacer" />
        <button type="button" className="btn ghost" onClick={() => { setAuth("student", null); navigate("/play"); }}>Sign out</button>
      </div>
      {error ? <Alert kind="error">{errorText(error)}</Alert> : null}
      {data?.report_ready && (
        <Link to="/play/report" className="btn big block">{t(lang, "home.report")}</Link>
      )}
      <h2>{t(lang, "home.levels")}</h2>
      {data && !data.sessions.length && <p className="muted">{t(lang, "home.no_schedule")}</p>}
      <div className="levels">
        {data?.sessions.map((s: any) => {
          const state = s.availability.state;
          const open = state === "available" || state === "in_progress";
          return (
            <div key={s.number} className={`level ${state === "completed" ? "done" : open ? "open" : ""}`}>
              <div className="num">{s.number}</div>
              <div className="small" style={{ minHeight: "2.6em" }}>
                {state === "completed" && <span className="badge good">✓ {t(lang, "completed")}</span>}
                {state === "upcoming" && t(lang, "upcoming", { date: formatDate(s.availability.opens_on, lang) })}
                {state === "missed" && <span className="badge">{t(lang, "missed")}</span>}
                {state === "locked" && <span className="muted">{t(lang, "locked")}</span>}
                {open && s.availability.makeup && <span className="muted">{t(lang, "makeup", { date: formatDate(s.availability.closes_on, lang) })}</span>}
              </div>
              {open && (
                <button type="button" className="btn block" onClick={() => navigate(`/play/session/${s.number}`)}>
                  {t(lang, state === "in_progress" ? "in_progress" : "available")}
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function StudentReport() {
  const auth = getAuth("student");
  const lang = useLang();
  const { data, error } = useAsync(() => api("GET", "/api/student/report", undefined, auth?.token), [auth?.token]);
  if (error) return <div className="page narrow"><Alert kind="error">{errorText(error)}</Alert></div>;
  if (!data) return <div className="page narrow"><p className="muted">{t(lang, "loading")}</p></div>;
  const r = data.content;
  return (
    <div className="page narrow stack">
      <h1>{r.title}</h1>
      <p>{r.intro}</p>
      <div className="card stack">
        <h2>{t(r.language, "report.strengths")}</h2>
        {r.strengths.map((s: any) => (
          <div key={s.skill_id} className="finding"><strong>{s.title}</strong><div>{s.text}</div></div>
        ))}
      </div>
      <div className="card stack">
        <h2>{t(r.language, "report.grow")}</h2>
        {r.areas_to_grow.map((s: any) => (
          <div key={s.skill_id} className="finding grow"><strong>{s.title}</strong><div>{s.text}</div></div>
        ))}
      </div>
      {r.action && <div className="card"><h2>{t(r.language, "report.action")}</h2><p style={{ fontSize: "1.2rem" }}>{r.action}</p></div>}
      {r.note && <div className="finding pattern">{r.note}</div>}
      <p className="disclaimer">{r.disclaimer}</p>
      <Link to="/play/home" className="btn secondary">{t(lang, "back")}</Link>
    </div>
  );
}
