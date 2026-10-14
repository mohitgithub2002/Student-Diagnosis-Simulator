import { useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, errorText, getAuth } from "../api";
import { Alert, Field, Loading, formatDate, useAsync } from "../components/ui";
import { StaffShell } from "../school/SchoolPages";

function useReviewer() {
  const navigate = useNavigate();
  const auth = getAuth("staff");
  if (!auth || !["reviewer", "superadmin"].includes(auth.role)) queueMicrotask(() => navigate("/admin"));
  return auth;
}

export function ReviewQueue() {
  const auth = useReviewer();
  const { data, error } = useAsync(() => api("GET", "/api/admin/review-queue", undefined, auth?.token), [auth?.token]);
  if (!auth) return null;
  return (
    <StaffShell area="admin">
      <h1>Review queue</h1>
      <p className="muted">Reports flagged by the automated wording or coverage check. Student identities are replaced by a reference.</p>
      {error ? <Alert kind="error">{errorText(error)}</Alert> : null}
      {!data && !error && <Loading />}
      {data && !data.length && <Alert kind="ok">Nothing to review.</Alert>}
      {data && data.length > 0 && (
        <div className="card table-wrap">
          <table className="data">
            <thead><tr><th>Student ref</th><th>Audience</th><th>Language</th><th>Flags</th><th>Created</th><th /></tr></thead>
            <tbody>
              {data.map((r: any) => (
                <tr key={r.id}>
                  <td><code>{r.student_ref}</code></td><td>{r.audience}</td><td>{r.language}</td>
                  <td>{r.flags.map((f: any, i: number) => <span key={i} className="badge warn" style={{ marginRight: 4 }}>{f.rule}{f.match ? `: ${f.match}` : ""}</span>)}</td>
                  <td>{formatDate(r.created_at)}</td>
                  <td><Link to={`/admin/review/${r.id}`}>Review</Link></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </StaffShell>
  );
}

export function ReviewReport() {
  const { reportId } = useParams();
  const auth = useReviewer();
  const navigate = useNavigate();
  const { data, error, reload } = useAsync(() => api("GET", `/api/admin/reports/${reportId}`, undefined, auth?.token), [reportId, auth?.token]);
  const [draft, setDraft] = useState<string | null>(null);
  const [msg, setMsg] = useState<{ kind: "ok" | "error"; text: string } | null>(null);
  if (!auth) return null;
  const json = draft ?? (data ? JSON.stringify(data.content, null, 2) : "");
  const save = async () => {
    try {
      const res = await api("PUT", `/api/admin/reports/${reportId}`, { content: JSON.parse(json) }, auth.token);
      setMsg({ kind: res.flags.length ? "error" : "ok", text: res.flags.length ? `Saved, still flagged: ${res.flags.map((f: any) => f.match || f.rule).join(", ")}` : "Saved. No flags remain." });
      setDraft(null);
      reload();
    } catch (e) {
      setMsg({ kind: "error", text: e instanceof SyntaxError ? "The JSON is not valid." : errorText(e) });
    }
  };
  const approve = async () => {
    try {
      await api("POST", `/api/admin/reports/${reportId}/approve`, undefined, auth.token);
      navigate("/admin/review");
    } catch (e) {
      setMsg({ kind: "error", text: errorText(e) });
    }
  };
  return (
    <StaffShell area="admin">
      <Link to="/admin/review">← Review queue</Link>
      {error ? <Alert kind="error">{errorText(error)}</Alert> : null}
      {!data && !error && <Loading />}
      {data && (
        <>
          <div className="row">
            <h1 style={{ margin: 0 }}>Report {data.id}</h1>
            <code>{data.student_ref}</code>
            <span className="badge">{data.audience} · {data.language} · v{data.scoring_version}</span>
            <span className="badge">{data.status}</span>
          </div>
          {data.flags.length > 0 && (
            <Alert kind="error">Flags: {data.flags.map((f: any) => `${f.rule}${f.match ? ` "${f.match}"` : ""} at ${f.path}`).join("; ")}</Alert>
          )}
          {msg && <Alert kind={msg.kind}>{msg.text}</Alert>}
          <div className="grid two">
            <div className="card">
              <h2>Preview</h2>
              <iframe title="Report preview" srcDoc={data.preview_html} style={{ width: "100%", height: 640, border: "1px solid #d9e1ea", borderRadius: 8 }} />
            </div>
            <div className="card stack">
              <h2>Edit content</h2>
              <p className="small muted">Edit wording only. <code>{"{name}"}</code> is filled in when the parent or student views the report.</p>
              <textarea value={json} onChange={(e) => setDraft(e.target.value)} style={{ minHeight: 520, fontFamily: "monospace", fontSize: "0.8rem" }} aria-label="Report JSON" />
              <div className="row">
                <button type="button" className="btn secondary" onClick={save} disabled={data.status === "released"}>Save edits and re-check</button>
                <span className="spacer" />
                <button type="button" className="btn" onClick={approve} disabled={data.status === "released"}>Approve and release</button>
              </div>
            </div>
          </div>
        </>
      )}
    </StaffShell>
  );
}

export function ItemBank() {
  const auth = useReviewer();
  const [filters, setFilters] = useState({ task_id: "T5", age_band: "11-14", language: "en", status: "" });
  const [selected, setSelected] = useState<any | null>(null);
  const query = useMemo(() => new URLSearchParams(Object.entries(filters).filter(([, v]) => v) as [string, string][]).toString(), [filters]);
  const tasks = useAsync(() => api("GET", "/api/admin/tasks", undefined, auth?.token), [auth?.token]);
  const items = useAsync(() => api("GET", `/api/admin/items?${query}&limit=200`, undefined, auth?.token), [query, auth?.token]);
  const stats = useAsync(() => api("GET", `/api/admin/items/stats?task_id=${filters.task_id}`, undefined, auth?.token), [filters.task_id, auth?.token]);
  const [msg, setMsg] = useState<string | null>(null);
  if (!auth) return null;
  const statBy = new Map<string, any>((stats.data ?? []).map((s: any) => [s.item_id, s]));
  const patch = async (id: string, body: Record<string, unknown>) => {
    try {
      await api("PATCH", `/api/admin/items/${id}`, body, auth.token);
      items.reload();
      setSelected(null);
    } catch (e) {
      setMsg(errorText(e));
    }
  };
  return (
    <StaffShell area="admin">
      <h1>Item bank</h1>
      <div className="card row">
        <Field label="Task">
          <select value={filters.task_id} onChange={(e) => setFilters({ ...filters, task_id: e.target.value })}>
            {tasks.data?.map((t: any) => <option key={t.id} value={t.id}>{t.id} {t.name} ({t.active_items})</option>)}
          </select>
        </Field>
        <Field label="Age band">
          <select value={filters.age_band} onChange={(e) => setFilters({ ...filters, age_band: e.target.value })}>
            <option value="11-14">11-14</option><option value="15-18">15-18</option>
          </select>
        </Field>
        <Field label="Language">
          <select value={filters.language} onChange={(e) => setFilters({ ...filters, language: e.target.value })}>
            <option value="">Any</option><option value="xx">Language-neutral</option><option value="en">English</option>
            <option value="hi">Hindi</option><option value="hinglish">Hinglish</option>
          </select>
        </Field>
        <Field label="Status">
          <select value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })}>
            <option value="">Any</option><option value="active">Active</option><option value="draft">Draft</option><option value="retired">Retired</option>
          </select>
        </Field>
      </div>
      <Alert kind="error">{msg}</Alert>
      {items.data && <p className="muted">{items.data.total} items</p>}
      <div className="grid two">
        <div className="card table-wrap" style={{ maxHeight: 640, overflowY: "auto" }}>
          <table className="data">
            <thead><tr><th>Item</th><th>Level</th><th>Status</th><th>Answered</th><th>% correct</th><th>Median time</th></tr></thead>
            <tbody>
              {items.data?.items.map((it: any) => {
                const s = statBy.get(it.id);
                return (
                  <tr key={it.id} onClick={() => setSelected(it)} style={{ cursor: "pointer", background: selected?.id === it.id ? "#eef3f8" : undefined }}>
                    <td><code>{it.id}</code></td><td>{it.level}</td>
                    <td><span className={`badge ${it.status === "active" ? "good" : it.status === "retired" ? "bad" : ""}`}>{it.status}</span></td>
                    <td>{s?.n ?? 0}</td><td>{s ? `${Math.round(s.p_correct * 100)}%` : "–"}</td>
                    <td>{s?.median_rt_ms ? `${(s.median_rt_ms / 1000).toFixed(1)}s` : "–"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <div className="card stack">
          {!selected ? <p className="muted">Select an item to see its content, tags and error statistics.</p> : (
            <>
              <h2><code>{selected.id}</code></h2>
              <div className="row">
                {selected.status !== "retired"
                  ? <button type="button" className="btn danger" onClick={() => patch(selected.id, { status: "retired" })}>Retire</button>
                  : <button type="button" className="btn" onClick={() => patch(selected.id, { status: "active" })}>Reactivate</button>}
                <TagEditor tags={selected.tags} onSave={(tags) => patch(selected.id, { tags })} />
              </div>
              {statBy.get(selected.id)?.error_tags && Object.keys(statBy.get(selected.id).error_tags).length > 0 && (
                <p>Root-cause tags: {Object.entries(statBy.get(selected.id).error_tags).map(([k, v]) => `${k} (${v})`).join(", ")}</p>
              )}
              <pre style={{ whiteSpace: "pre-wrap", fontSize: "0.8rem", background: "#f7f9fc", padding: "0.75rem", borderRadius: 8, maxHeight: 460, overflow: "auto" }}>
                {JSON.stringify({ content: selected.content, answer_key: selected.answer_key, variant_group: selected.variant_group }, null, 2)}
              </pre>
            </>
          )}
        </div>
      </div>
    </StaffShell>
  );
}

function TagEditor({ tags, onSave }: { tags: string[]; onSave: (tags: string[]) => void }) {
  const [value, setValue] = useState(tags.join(", "));
  return (
    <div className="row" style={{ flex: 1 }}>
      <input type="text" value={value} onChange={(e) => setValue(e.target.value)} aria-label="Tags" style={{ flex: 1 }} />
      <button type="button" className="btn secondary" onClick={() => onSave(value.split(",").map((t) => t.trim()).filter(Boolean))}>Save tags</button>
    </div>
  );
}

export function ScoringConfigs() {
  const auth = useReviewer();
  const { data, error, reload } = useAsync(() => api("GET", "/api/admin/scoring-configs", undefined, auth?.token), [auth?.token]);
  const [version, setVersion] = useState("");
  const [notes, setNotes] = useState("");
  const [json, setJson] = useState("");
  const [msg, setMsg] = useState<{ kind: "ok" | "error"; text: string } | null>(null);
  if (!auth) return null;
  const active = data?.find((c: any) => c.active);
  const create = async () => {
    try {
      await api("POST", "/api/admin/scoring-configs", { version, notes, config: JSON.parse(json || JSON.stringify(active?.config ?? {})) }, auth.token);
      setMsg({ kind: "ok", text: `Version ${version} saved (inactive).` });
      reload();
    } catch (e) {
      setMsg({ kind: "error", text: e instanceof SyntaxError ? "The JSON is not valid." : errorText(e) });
    }
  };
  const activate = async (v: string) => {
    try {
      await api("POST", `/api/admin/scoring-configs/${v}/activate`, undefined, auth.token);
      reload();
    } catch (e) {
      setMsg({ kind: "error", text: errorText(e) });
    }
  };
  return (
    <StaffShell area="admin">
      <h1>Scoring configuration</h1>
      <p className="muted">Weights and thresholds are versioned. Every score and report records the version it used, so any report can be traced. Thresholds marked "pilot" are placeholders until pilot data sets them.</p>
      {error ? <Alert kind="error">{errorText(error)}</Alert> : null}
      {msg && <Alert kind={msg.kind}>{msg.text}</Alert>}
      <div className="card table-wrap">
        <table className="data">
          <thead><tr><th>Version</th><th>Status</th><th>Notes</th><th>Created</th><th /></tr></thead>
          <tbody>
            {data?.map((c: any) => (
              <tr key={c.version}>
                <td><code>{c.version}</code></td>
                <td>{c.active ? <span className="badge good">active</span> : <span className="badge">inactive</span>}</td>
                <td>{c.notes}</td><td>{formatDate(c.created_at)} · {c.created_by}</td>
                <td className="row">
                  <button type="button" className="btn ghost" onClick={() => { setJson(JSON.stringify(c.config, null, 2)); setVersion(""); }}>Copy to editor</button>
                  {!c.active && auth.role === "superadmin" && <button type="button" className="btn secondary" onClick={() => activate(c.version)}>Activate</button>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="card stack">
        <h2>New version</h2>
        <div className="row">
          <Field label="Version (x.y.z)"><input type="text" value={version} onChange={(e) => setVersion(e.target.value)} placeholder="1.1.0" /></Field>
          <Field label="Notes"><input type="text" value={notes} onChange={(e) => setNotes(e.target.value)} /></Field>
        </div>
        <textarea value={json} onChange={(e) => setJson(e.target.value)} placeholder="Copy a version to the editor, then change weights or thresholds"
          style={{ minHeight: 360, fontFamily: "monospace", fontSize: "0.8rem" }} aria-label="Scoring config JSON" />
        <button type="button" className="btn" disabled={!/^\d+\.\d+\.\d+$/.test(version)} onClick={create}>Save as new version</button>
      </div>
    </StaffShell>
  );
}

export function Quality() {
  const auth = useReviewer();
  const rel = useAsync(() => api("GET", "/api/admin/reliability", undefined, auth?.token), [auth?.token]);
  if (!auth) return null;
  return (
    <StaffShell area="admin">
      <h1>Quality</h1>
      <div className="card stack">
        <h2>Retest reliability</h2>
        <p className="muted">Pilot target: correlation of 0.7 or higher between first and repeat measurements (T1, T3, T17).</p>
        {!rel.data && <Loading />}
        {rel.data && (
          <div className="table-wrap">
            <table className="data">
              <thead><tr><th>Measure</th><th>Sessions</th><th>Students</th><th>Correlation</th></tr></thead>
              <tbody>
                {Object.entries(rel.data).map(([name, r]: [string, any]) => (
                  <tr key={name}><td><code>{name}</code></td><td>{r.sessions.join(" vs ")}</td><td>{r.n}</td>
                    <td>{r.r === null ? <span className="muted">needs 3+ students</span> : <span className={`badge ${r.r >= 0.7 ? "good" : "warn"}`}>{r.r}</span>}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </StaffShell>
  );
}

export function AuditLog() {
  const auth = useReviewer();
  const { data, error } = useAsync(() => api("GET", "/api/admin/audit?limit=300", undefined, auth?.token), [auth?.token]);
  if (!auth) return null;
  return (
    <StaffShell area="admin">
      <h1>Audit log</h1>
      {error ? <Alert kind="error">{errorText(error)}</Alert> : null}
      <div className="card table-wrap">
        <table className="data">
          <thead><tr><th>When</th><th>Actor</th><th>Action</th><th>Target</th></tr></thead>
          <tbody>
            {data?.map((r: any, i: number) => (
              <tr key={i}><td>{new Date(r.at).toLocaleString("en-IN")}</td><td>{r.actor_role}</td><td>{r.action}</td><td>{r.target_type} {r.target_id}</td></tr>
            ))}
          </tbody>
        </table>
      </div>
    </StaffShell>
  );
}
