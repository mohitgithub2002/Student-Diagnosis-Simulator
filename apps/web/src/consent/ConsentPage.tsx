import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api, errorText, setAuth } from "../api";
import { Alert, Field, Loading, Topbar, useAsync } from "../components/ui";

const TEXT = {
  en: {
    heading: "Consent for {name}", verify: "Verify it's you", send: "Send code to {phone}", code: "6-digit code",
    save: "Save my choices", saved: "Thank you. Your choices are saved.", portal: "Go to the parent portal",
    yes: "Yes", no: "No", choices: "Your choices", lang: "हिंदी में पढ़ें",
  },
  hi: {
    heading: "{name} के लिए सहमति", verify: "पुष्टि करें कि यह आप हैं", send: "{phone} पर कोड भेजें", code: "6 अंकों का कोड",
    save: "मेरे विकल्प सहेजें", saved: "धन्यवाद। आपके विकल्प सहेज लिए गए हैं।", portal: "अभिभावक पोर्टल पर जाएँ",
    yes: "हाँ", no: "नहीं", choices: "आपके विकल्प", lang: "Read in English",
  },
};

/** Parent consent from the SMS link (FR-03): plain-language notice, OTP, separate choices. */
export function ConsentPage() {
  const { token } = useParams();
  const navigate = useNavigate();
  const { data, error } = useAsync(() => api("GET", `/api/consent/${token}`), [token]);
  const [lang, setLang] = useState<"en" | "hi" | null>(null);
  const [participate, setParticipate] = useState<boolean | null>(null);
  const [voice, setVoice] = useState(false);
  const [share, setShare] = useState(false);
  const [code, setCode] = useState("");
  const [sent, setSent] = useState(false);
  const [msg, setMsg] = useState<{ kind: "error" | "ok"; text: string } | null>(null);
  const [done, setDone] = useState<string | null>(null);

  if (error) return <><Topbar title="Consent" /><div className="page narrow"><Alert kind="error">{errorText(error)}</Alert></div></>;
  if (!data) return <><Topbar title="Consent" /><div className="page narrow"><Loading /></div></>;
  const l = lang ?? (data.language as "en" | "hi");
  const T = TEXT[l];
  const notice = data.notice[l];
  const fill = (s: string) => s.replace("{name}", data.student_first_name).replace("{phone}", data.phone_hint);

  const submit = async () => {
    setMsg(null);
    try {
      const res = await api("POST", `/api/consent/${token}`, {
        code, participate, voice: participate ? voice : false, share_with_school: participate ? share : false, language: l,
      });
      setAuth("parent", { token: res.token, role: "parent" });
      setDone(res.state);
    } catch (e) {
      setMsg({ kind: "error", text: errorText(e) });
    }
  };

  return (
    <>
      <Topbar title={data.school} right={<button type="button" className="link" style={{ color: "#fff" }} onClick={() => setLang(l === "en" ? "hi" : "en")}>{T.lang}</button>} />
      <div className="page narrow stack" lang={l}>
        <h1>{fill(T.heading)}</h1>
        <div className="card stack">
          <h2>{notice.title}</h2>
          {notice.paragraphs.map((p: string, i: number) => <p key={i}>{p}</p>)}
          <p className="small muted">Notice {data.notice_version}</p>
        </div>
        {done ? (
          <div className="card stack">
            <Alert kind="ok">{T.saved}</Alert>
            <button type="button" className="btn" onClick={() => navigate("/parent/home")}>{T.portal}</button>
          </div>
        ) : (
          <div className="card stack">
            <h2>{T.choices}</h2>
            <fieldset className="stack" style={{ border: "none", padding: 0 }}>
              <legend><strong>{notice.choices.participate}</strong></legend>
              <div className="row">
                <button type="button" className={`btn ${participate === true ? "" : "secondary"}`} aria-pressed={participate === true}
                  onClick={() => setParticipate(true)}>{T.yes}</button>
                <button type="button" className={`btn ${participate === false ? "" : "secondary"}`} aria-pressed={participate === false}
                  onClick={() => setParticipate(false)}>{T.no}</button>
              </div>
            </fieldset>
            {participate && (
              <>
                <label className="check"><input type="checkbox" checked={voice} onChange={(e) => setVoice(e.target.checked)} />
                  <span>{notice.choices.voice}</span></label>
                <label className="check"><input type="checkbox" checked={share} onChange={(e) => setShare(e.target.checked)} />
                  <span>{notice.choices.share_with_school}</span></label>
              </>
            )}
            <h3>{T.verify}</h3>
            <button type="button" className="btn secondary" onClick={async () => {
              try { await api("POST", `/api/consent/${token}/otp`); setSent(true); } catch (e) { setMsg({ kind: "error", text: errorText(e) }); }
            }}>{fill(T.send)}</button>
            {sent && (
              <Field label={T.code}>
                <input type="text" inputMode="numeric" maxLength={6} value={code} onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))} />
              </Field>
            )}
            {msg && <Alert kind={msg.kind}>{msg.text}</Alert>}
            <button type="button" className="btn big" disabled={participate === null || code.length !== 6} onClick={submit}>{T.save}</button>
          </div>
        )}
      </div>
    </>
  );
}
