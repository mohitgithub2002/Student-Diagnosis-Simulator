import { useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, errorText, getAuth, setAuth, upload } from "../api";
import { Alert, Field, Loading, Topbar, formatDate, useAsync } from "../components/ui";
import { ReportView } from "../report/ReportView";

export function StaffShell({ area, children }: { area: "school" | "admin"; children: React.ReactNode }) {
  const navigate = useNavigate();
  const auth = getAuth("staff");
  const links = area === "school"
    ? [{ to: "/school/dashboard", label: "Dashboard" }, { to: "/school/reports", label: "Shared reports" }]
    : [{ to: "/admin/review", label: "Review queue" }, { to: "/admin/items", label: "Item bank" },
      { to: "/admin/scoring", label: "Scoring" }, { to: "/admin/quality", label: "Quality" },
      ...(auth?.role === "superadmin" ? [{ to: "/admin/audit", label: "Audit log" }] : [])];
  return (
    <>
      <Topbar title={area === "school" ? "School portal" : "Admin console"} links={auth ? links : []}
        right={auth && <button type="button" className="link" style={{ color: "#fff" }}
          onClick={() => { setAuth("staff", null); navigate(area === "school" ? "/school" : "/admin"); }}>Sign out</button>} />
      <div className="page stack">{children}</div>
    </>
  );
}

export function StaffLogin({ area }: { area: "school" | "admin" }) {
  const navigate = useNavigate();
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [form, setForm] = useState({ email: "", password: "", school_name: "", city: "", admin_name: "" });
  const [error, setError] = useState<string | null>(null);
  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) => setForm({ ...form, [k]: e.target.value });
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      const res = mode === "login"
        ? await api("POST", "/api/auth/staff/login", { email: form.email, password: form.password })
        : await api("POST", "/api/auth/school-signup", {
          school_name: form.school_name, city: form.city, admin_name: form.admin_name, admin_email: form.email,
          admin_password: form.password,
        });
      setAuth("staff", { token: res.token, role: res.role, name: res.name, school_id: res.school_id });
      navigate(["reviewer", "superadmin"].includes(res.role) ? "/admin/review" : "/school/dashboard");
    } catch (err) {
      setError(errorText(err));
    }
  };
  return (
    <StaffShell area={area}>
      <div className="card stack" style={{ maxWidth: 520 }}>
        <h1>{mode === "login" ? (area === "school" ? "School sign in" : "Reviewer sign in") : "Register your school"}</h1>
        <form className="stack" onSubmit={submit}>
          {mode === "signup" && (
            <>
              <Field label="School name"><input type="text" value={form.school_name} onChange={set("school_name")} required /></Field>
              <Field label="City"><input type="text" value={form.city} onChange={set("city")} /></Field>
              <Field label="Your name"><input type="text" value={form.admin_name} onChange={set("admin_name")} required /></Field>
            </>
          )}
          <Field label="Email"><input type="email" value={form.email} onChange={set("email")} required autoComplete="username" /></Field>
          <Field label="Password" hint={mode === "signup" ? "At least 8 characters" : undefined}>
            <input type="password" value={form.password} onChange={set("password")} required minLength={mode === "signup" ? 8 : 1}
              autoComplete={mode === "login" ? "current-password" : "new-password"} />
          </Field>
          <Alert kind="error">{error}</Alert>
          <button className="btn">{mode === "login" ? "Sign in" : "Create school account"}</button>
        </form>
        {area === "school" && (
          <button type="button" className="link" onClick={() => setMode(mode === "login" ? "signup" : "login")}>
            {mode === "login" ? "New school? Register here" : "Already registered? Sign in"}
          </button>
        )}
      </div>
    </StaffShell>
  );
}

function useStaff() {
  const navigate = useNavigate();
  const auth = getAuth("staff");
  if (!auth) {
    queueMicrotask(() => navigate("/school"));
  }
  return auth;
}

export function SchoolDashboard() {
  const auth = useStaff();
  const school = useAsync(() => api("GET", "/api/school", undefined, auth?.token), [auth?.token]);
  const dash = useAsync(() => api("GET", "/api/school/dashboard", undefined, auth?.token), [auth?.token]);
  const [form, setForm] = useState({ grade: "", section: "", age_band: "11-14" });
  const [error, setError] = useState<string | null>(null);
  const isAdmin = auth?.role === "school_admin";
  const addClass = async (e: FormEvent) => {
    e.preventDefault();
    try {
      await api("POST", "/api/school/classes", form, auth?.token);
      setForm({ grade: "", section: "", age_band: "11-14" });
      school.reload();
      dash.reload();
    } catch (err) {
      setError(errorText(err));
    }
  };
  if (!auth) return null;
  return (
    <StaffShell area="school">
      <h1>{school.data?.name ?? "Dashboard"}</h1>
      <p className="muted">Enrolment, consent and completion by class. Individual reports appear only when a parent chooses to share them.</p>
      {(school.error || dash.error) ? <Alert kind="error">{errorText(school.error ?? dash.error)}</Alert> : null}
      {!dash.data && <Loading />}
      <div className="grid two">
        {dash.data?.classes.map((c: any) => {
          const info = school.data?.classes.find((x: any) => x.id === c.id);
          return (
            <div key={c.id} className="card stack">
              <div className="row">
                <h2 style={{ margin: 0 }}>Class {c.grade}{c.section}</h2>
                <span className="badge">Ages {c.age_band}</span>
                <span className="spacer" />
                {info && <span className="badge" title="Students sign in with this code">Code {info.class_code}</span>}
              </div>
              <div className="row small">
                <span><strong>{c.enrolled}</strong> enrolled</span>
                <span className="badge good">{c.consent.yes} consented</span>
                <span className="badge">{c.consent.pending} pending</span>
                {c.consent.no > 0 && <span className="badge warn">{c.consent.no} declined</span>}
                {c.consent.withdrawn > 0 && <span className="badge bad">{c.consent.withdrawn} withdrawn</span>}
              </div>
              <div>
                <div className="small muted">Students by sessions completed (0 to 7)</div>
                <Histogram data={c.sessions_completed_histogram} />
              </div>
              <div className="row small">
                <span>Completed all 7: <strong>{c.completed_all}</strong> ({Math.round(c.completion_rate * 100)}%)</span>
                <span>Reports ready: <strong>{c.reports_ready}</strong></span>
                <span className="muted">{c.cycle_start ? `Cycle from ${formatDate(c.cycle_start)}` : "Not scheduled"}</span>
              </div>
              <Link className="btn secondary" to={`/school/class/${c.id}`}>Open class</Link>
            </div>
          );
        })}
      </div>
      {isAdmin && (
        <div className="grid two">
          <form className="card stack" onSubmit={addClass}>
            <h2>Add a class</h2>
            <div className="row">
              <Field label="Grade"><input type="text" value={form.grade} onChange={(e) => setForm({ ...form, grade: e.target.value })} required /></Field>
              <Field label="Section"><input type="text" value={form.section} onChange={(e) => setForm({ ...form, section: e.target.value })} /></Field>
            </div>
            <Field label="Age band">
              <select value={form.age_band} onChange={(e) => setForm({ ...form, age_band: e.target.value })}>
                <option value="11-14">11 to 14</option>
                <option value="15-18">15 to 18</option>
              </select>
            </Field>
            <Alert kind="error">{error}</Alert>
            <button className="btn">Create class</button>
          </form>
          <AddTeacher token={auth.token} />
        </div>
      )}
    </StaffShell>
  );
}

function Histogram({ data }: { data: Record<string, number> }) {
  const max = Math.max(1, ...Object.values(data));
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(8, 1fr)", gap: 4, alignItems: "end", height: 70 }}
      role="img" aria-label={Object.entries(data).map(([k, v]) => `${v} students with ${k} sessions`).join(", ")}>
      {Object.entries(data).map(([k, v]) => (
        <div key={k} style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 2 }}>
          <span className="small">{v || ""}</span>
          <div style={{ width: "100%", height: `${(v / max) * 44}px`, minHeight: v ? 4 : 1, background: k === "7" ? "#2e7d4f" : "#2f6f9f", borderRadius: 4 }} />
          <span className="small muted">{k}</span>
        </div>
      ))}
    </div>
  );
}

function AddTeacher({ token }: { token: string }) {
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [msg, setMsg] = useState<{ kind: "ok" | "error"; text: string } | null>(null);
  return (
    <form className="card stack" onSubmit={async (e) => {
      e.preventDefault();
      try {
        await api("POST", "/api/school/teachers", form, token);
        setMsg({ kind: "ok", text: `Teacher account created for ${form.email}` });
        setForm({ name: "", email: "", password: "" });
      } catch (err) {
        setMsg({ kind: "error", text: errorText(err) });
      }
    }}>
      <h2>Add a teacher</h2>
      <Field label="Name"><input type="text" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required /></Field>
      <Field label="Email"><input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required /></Field>
      <Field label="Temporary password"><input type="password" value={form.password} minLength={8} onChange={(e) => setForm({ ...form, password: e.target.value })} required /></Field>
      {msg && <Alert kind={msg.kind}>{msg.text}</Alert>}
      <button className="btn secondary">Create teacher</button>
    </form>
  );
}

export function ClassPage() {
  const { classId } = useParams();
  const auth = useStaff();
  const roster = useAsync(() => api("GET", `/api/school/classes/${classId}/roster`, undefined, auth?.token), [classId, auth?.token]);
  const [file, setFile] = useState<File | null>(null);
  const [pins, setPins] = useState<{ name: string; pin: string }[] | null>(null);
  const [msg, setMsg] = useState<{ kind: "ok" | "error"; text: string } | null>(null);
  const [start, setStart] = useState(new Date().toISOString().slice(0, 10));
  const [mode, setMode] = useState("lab");
  const isAdmin = auth?.role === "school_admin";
  if (!auth) return null;

  const doUpload = async () => {
    if (!file) return;
    try {
      const res = await upload(`/api/school/classes/${classId}/students/upload`, file, auth.token);
      setPins(res.created);
      setMsg({ kind: res.errors.length ? "error" : "ok", text: `${res.created.length} students added. Consent links sent to parents.${res.errors.length ? ` ${res.errors.length} rows had problems: ${res.errors.map((e: any) => `line ${e.line}`).join(", ")}` : ""}` });
      roster.reload();
    } catch (e) {
      setMsg({ kind: "error", text: errorText(e) });
    }
  };
  const doSchedule = async () => {
    try {
      const res = await api("POST", `/api/school/classes/${classId}/schedule`, { start_date: start, mode }, auth.token);
      setMsg({ kind: "ok", text: `Cycle scheduled from ${formatDate(res.cycle_start)}: 7 sessions, one every second day, each with a 3-day catch-up window.` });
      roster.reload();
    } catch (e) {
      setMsg({ kind: "error", text: errorText(e) });
    }
  };
  const action = async (path: string, done: (r: any) => void) => {
    try {
      done(await api("POST", path, undefined, auth.token));
    } catch (e) {
      setMsg({ kind: "error", text: errorText(e) });
    }
  };
  const cls = roster.data?.class;
  return (
    <StaffShell area="school">
      <Link to="/school/dashboard">← Dashboard</Link>
      <h1>{cls ? `Class ${cls.grade}${cls.section}` : "Class"}</h1>
      {cls && <p>Students sign in with class code <strong>{cls.class_code}</strong> and their own 4-digit PIN.</p>}
      {msg && <Alert kind={msg.kind}>{msg.text}</Alert>}
      {pins && pins.length > 0 && (
        <div className="card stack">
          <h2>New PINs (shown once)</h2>
          <p className="muted small">Print or note these now. Only a protected version is stored, so they cannot be shown again (you can reset a PIN).</p>
          <div className="table-wrap"><table className="data"><thead><tr><th>Student</th><th>PIN</th></tr></thead>
            <tbody>{pins.map((p) => <tr key={p.name}><td>{p.name}</td><td><code>{p.pin}</code></td></tr>)}</tbody></table></div>
          <button type="button" className="btn secondary" onClick={() => window.print()}>Print</button>
        </div>
      )}
      {isAdmin && (
        <div className="grid two">
          <div className="card stack">
            <h2>Upload class list</h2>
            <p className="small muted">CSV columns: <code>name, parent_phone</code>, optional <code>parent_language</code> (en/hi) and <code>student_language</code> (en/hi/hinglish).</p>
            <input type="file" accept=".csv,text/csv" onChange={(e) => setFile(e.target.files?.[0] ?? null)} aria-label="Class list CSV" />
            <button type="button" className="btn" disabled={!file} onClick={doUpload}>Upload and send consent links</button>
          </div>
          <div className="card stack">
            <h2>Schedule sessions</h2>
            <Field label="Start date"><input type="date" value={start} onChange={(e) => setStart(e.target.value)} /></Field>
            <Field label="Where sessions run">
              <select value={mode} onChange={(e) => setMode(e.target.value)}>
                <option value="lab">School lab periods</option>
                <option value="home">At home</option>
                <option value="both">Both</option>
              </select>
            </Field>
            <button type="button" className="btn" onClick={doSchedule}>Schedule 7 sessions</button>
          </div>
        </div>
      )}
      <div className="card">
        <h2>Consent and completion</h2>
        {!roster.data && <Loading />}
        {roster.data && (
          <div className="table-wrap">
            <table className="data">
              <thead><tr><th>Student</th><th>Consent</th><th>Sessions</th><th>Report shared</th>{isAdmin && <th>Actions</th>}</tr></thead>
              <tbody>
                {roster.data.students.map((s: any) => (
                  <tr key={s.student_id}>
                    <td>{s.name}</td>
                    <td><span className={`badge ${s.consent === "yes" ? "good" : s.consent === "pending" ? "" : "warn"}`}>{s.consent}</span></td>
                    <td>{s.sessions_completed} / 7</td>
                    <td>{s.shared_with_school ? <Link to={`/school/reports/${s.student_id}`}>Open</Link> : <span className="muted">No</span>}</td>
                    {isAdmin && (
                      <td className="row" style={{ gap: "0.4rem" }}>
                        <button type="button" className="btn ghost" onClick={() => action(`/api/school/students/${s.student_id}/pin`,
                          (r) => setPins([{ name: s.name, pin: r.pin }]))}>Reset PIN</button>
                        {s.consent === "pending" && (
                          <button type="button" className="btn ghost" onClick={() => action(`/api/school/students/${s.student_id}/consent-link`,
                            () => setMsg({ kind: "ok", text: `Consent link re-sent for ${s.name}` }))}>Resend link</button>
                        )}
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </StaffShell>
  );
}

export function SharedReports() {
  const auth = useStaff();
  const { data, error } = useAsync(() => api("GET", "/api/school/reports", undefined, auth?.token), [auth?.token]);
  if (!auth) return null;
  return (
    <StaffShell area="school">
      <h1>Reports shared by parents</h1>
      <p className="muted">Only reports that parents chose to share with the school appear here.</p>
      {error ? <Alert kind="error">{errorText(error)}</Alert> : null}
      {data && !data.length && <p className="muted">No shared reports yet.</p>}
      {data && data.length > 0 && (
        <div className="card table-wrap">
          <table className="data"><thead><tr><th>Student</th><th>Class</th><th>Released</th><th /></tr></thead>
            <tbody>{data.map((r: any) => (
              <tr key={r.student_id}><td>{r.name}</td><td>{r.class}</td><td>{formatDate(r.released_at)}</td>
                <td><Link to={`/school/reports/${r.student_id}`}>Open</Link></td></tr>
            ))}</tbody></table>
        </div>
      )}
    </StaffShell>
  );
}

export function SharedReport() {
  const { studentId } = useParams();
  const auth = useStaff();
  const { data, error } = useAsync(() => api("GET", `/api/school/reports/${studentId}`, undefined, auth?.token), [studentId, auth?.token]);
  if (!auth) return null;
  return (
    <StaffShell area="school">
      <Link to="/school/reports">← Shared reports</Link>
      {error ? <Alert kind="error">{errorText(error)}</Alert> : null}
      {!data && !error && <Loading />}
      {data && <ReportView content={data.content} />}
    </StaffShell>
  );
}
