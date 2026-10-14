import { useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, download, errorText, getAuth, setAuth } from "../api";
import { Alert, Field, Loading, Topbar, formatDate, useAsync } from "../components/ui";
import { ReportView } from "../report/ReportView";

function ParentShell({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate();
  return (
    <>
      <Topbar title="Parent portal" links={[{ to: "/parent/home", label: "My children" }]}
        right={getAuth("parent") && <button type="button" className="link" style={{ color: "#fff" }}
          onClick={() => { setAuth("parent", null); navigate("/parent"); }}>Sign out</button>} />
      <div className="page stack">{children}</div>
    </>
  );
}

export function ParentLogin() {
  const navigate = useNavigate();
  const [phone, setPhone] = useState("");
  const [code, setCode] = useState("");
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const request = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await api("POST", "/api/auth/parent/otp", { phone });
      setSent(true);
    } catch (err) {
      setError(errorText(err));
    }
  };
  const verify = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      const res = await api("POST", "/api/auth/parent/verify", { phone, code });
      setAuth("parent", { token: res.token, role: "parent" });
      navigate("/parent/home");
    } catch (err) {
      setError(errorText(err));
    }
  };
  return (
    <ParentShell>
      <div className="card stack" style={{ maxWidth: 480 }}>
        <h1>Sign in with your phone</h1>
        <p className="muted">We send a one-time code to the phone number your child's school has on record. / स्कूल में दर्ज फ़ोन नंबर पर एक कोड भेजा जाएगा।</p>
        <form className="stack" onSubmit={sent ? verify : request}>
          <Field label="Mobile number / मोबाइल नंबर">
            <input type="tel" value={phone} onChange={(e) => setPhone(e.target.value)} required disabled={sent} autoComplete="tel" />
          </Field>
          {sent && (
            <Field label="6-digit code / 6 अंकों का कोड">
              <input type="text" inputMode="numeric" maxLength={6} value={code} onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))} required autoFocus />
            </Field>
          )}
          <Alert kind="error">{error}</Alert>
          <button className="btn">{sent ? "Verify" : "Send code"}</button>
        </form>
      </div>
    </ParentShell>
  );
}

export function ParentHome() {
  const auth = getAuth("parent");
  const navigate = useNavigate();
  const { data, error, reload } = useAsync(() => api("GET", "/api/parent/children", undefined, auth?.token), [auth?.token]);
  if (!auth) {
    navigate("/parent");
    return null;
  }
  return (
    <ParentShell>
      <h1>My children</h1>
      {error ? <Alert kind="error">{errorText(error)}</Alert> : null}
      {!data && !error && <Loading />}
      {data?.length === 0 && <p className="muted">No children are linked to this phone number.</p>}
      {data?.map((c: any) => <ChildCard key={c.student_id} child={c} token={auth.token} onChange={reload} />)}
    </ParentShell>
  );
}

function ChildCard({ child: c, token, onChange }: { child: any; token: string; onChange: () => void }) {
  const [voice, setVoice] = useState<boolean>(c.consent.voice);
  const [share, setShare] = useState<boolean>(c.consent.share_with_school);
  const [lang, setLang] = useState<"en" | "hi">(c.language);
  const [msg, setMsg] = useState<{ kind: "ok" | "error"; text: string } | null>(null);
  const [confirm, setConfirm] = useState(false);
  const participating = c.consent.state === "yes";
  const save = async (participate: boolean) => {
    try {
      await api("POST", `/api/parent/children/${c.student_id}/consent`, { participate, voice, share_with_school: share, language: lang }, token);
      setMsg({ kind: "ok", text: "Saved." });
      onChange();
    } catch (e) {
      setMsg({ kind: "error", text: errorText(e) });
    }
  };
  const withdraw = async () => {
    try {
      await api("POST", `/api/parent/children/${c.student_id}/withdraw`, undefined, token);
      onChange();
    } catch (e) {
      setMsg({ kind: "error", text: errorText(e) });
    }
  };
  const pct = Math.round((c.progress.sessions_completed / c.progress.sessions_total) * 100);
  return (
    <div className="card stack">
      <div className="row">
        <h2 style={{ margin: 0 }}>{c.name}</h2>
        <span className="muted">{c.school} · Class {c.class}</span>
        <span className="spacer" />
        <span className={`badge ${participating ? "good" : "warn"}`}>Consent: {c.consent.state}</span>
      </div>
      <div>
        <div className="row small"><span>Sessions completed: {c.progress.sessions_completed} of 7</span>
          {c.progress.next_session && <span className="muted">Next: {formatDate(c.progress.next_session)}</span>}</div>
        <div className="bar" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}><span style={{ width: `${pct}%` }} /></div>
      </div>
      {c.report_ready ? (
        <Link to={`/parent/report/${c.student_id}`} className="btn">View report / रिपोर्ट देखें</Link>
      ) : <p className="muted small">The report will be ready shortly after session 7.</p>}
      <details>
        <summary><strong>Consent and privacy choices</strong></summary>
        <div className="stack" style={{ marginTop: "0.75rem" }}>
          <label className="check"><input type="checkbox" checked={voice} onChange={(e) => setVoice(e.target.checked)} />
            <span>Use the microphone for reading and speaking activities (only numbers are kept)</span></label>
          <label className="check"><input type="checkbox" checked={share} onChange={(e) => setShare(e.target.checked)} />
            <span>Share the individual report with the school</span></label>
          <Field label="Report language">
            <select value={lang} onChange={(e) => setLang(e.target.value as "en" | "hi")}>
              <option value="en">English</option>
              <option value="hi">हिंदी</option>
            </select>
          </Field>
          <div className="row">
            <button type="button" className="btn" onClick={() => save(true)}>{participating ? "Save choices" : "Allow participation"}</button>
            {participating && !confirm && <button type="button" className="btn danger" onClick={() => setConfirm(true)}>Withdraw consent</button>}
          </div>
          {confirm && (
            <div className="alert error stack">
              <p><strong>Withdraw and delete all data?</strong> All of {c.name}'s assessment data will be deleted and you will get a confirmation message. This cannot be undone.</p>
              <div className="row">
                <button type="button" className="btn danger" onClick={withdraw}>Yes, withdraw and delete</button>
                <button type="button" className="btn secondary" onClick={() => setConfirm(false)}>Cancel</button>
              </div>
            </div>
          )}
          {msg && <Alert kind={msg.kind}>{msg.text}</Alert>}
          {c.consent.notice_version && <p className="small muted">Notice version {c.consent.notice_version}, given {formatDate(c.consent.given_at)}</p>}
        </div>
      </details>
    </div>
  );
}

export function ParentReport() {
  const { studentId } = useParams();
  const auth = getAuth("parent");
  const [lang, setLang] = useState<string | null>(null);
  const { data, error } = useAsync(
    () => api("GET", `/api/parent/children/${studentId}/report${lang ? `?lang=${lang}` : ""}`, undefined, auth?.token),
    [studentId, lang, auth?.token],
  );
  const [dlError, setDlError] = useState<string | null>(null);
  return (
    <ParentShell>
      <div className="row">
        <Link to="/parent/home">← Back</Link>
        <span className="spacer" />
        <div className="row" role="group" aria-label="Report language">
          <button type="button" className={`btn ${data?.content.language === "en" ? "" : "secondary"}`} onClick={() => setLang("en")}>English</button>
          <button type="button" className={`btn ${data?.content.language === "hi" ? "" : "secondary"}`} onClick={() => setLang("hi")}>हिंदी</button>
        </div>
        <button type="button" className="btn secondary" onClick={() =>
          download(`/api/parent/children/${studentId}/report?fmt=pdf${lang ? `&lang=${lang}` : ""}`, auth!.token, "profile-report.pdf").catch((e) => setDlError(errorText(e)))}>
          Download PDF
        </button>
      </div>
      <Alert kind="error">{dlError}</Alert>
      {error ? <Alert kind="error">{errorText(error)}</Alert> : null}
      {!data && !error && <Loading />}
      {data && <ReportView content={data.content} />}
    </ParentShell>
  );
}
