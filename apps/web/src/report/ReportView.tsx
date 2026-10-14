/** Renders a parent report (structured JSON from the API) for parents, shared-school views and reviewers. */
const LABELS = {
  en: {
    strengths: "Strengths", areas: "Areas to grow", patterns: "Patterns worth knowing", causes: "What was behind missed answers",
    skills: "All 24 skills, compared with the student's own average", early: "Early signals", notes: "Notes for a teacher or counsellor",
    evidence: "Evidence", home: "At home", school: "At school", clear: "clear strength", version: "Scoring version",
    level: { High: "High evidence", Medium: "Likely (medium evidence)", Low: "Early signal" } as Record<string, string>,
    adjusted: "* language-adjusted", none_s: "Strengths will be clearer after the next cycle.", none_a: "No clear area to grow stood out this cycle.",
  },
  hi: {
    strengths: "खूबियाँ", areas: "आगे बढ़ने के क्षेत्र", patterns: "जानने लायक पैटर्न", causes: "छूटे उत्तरों के पीछे क्या था",
    skills: "सभी 24 कौशल, अपने औसत की तुलना में", early: "शुरुआती संकेत", notes: "शिक्षक या काउंसलर के लिए नोट्स",
    evidence: "प्रमाण", home: "घर पर", school: "स्कूल में", clear: "स्पष्ट खूबी", version: "स्कोरिंग संस्करण",
    level: { High: "मज़बूत प्रमाण", Medium: "संभावित (मध्यम प्रमाण)", Low: "शुरुआती संकेत" } as Record<string, string>,
    adjusted: "* भाषा-समायोजित", none_s: "अगले चक्र के बाद खूबियाँ और साफ़ दिखेंगी।", none_a: "इस चक्र में आगे बढ़ने का कोई साफ़ क्षेत्र नहीं दिखा।",
  },
};

export function ReportView({ content: r }: { content: any }) {
  const L = LABELS[(r.language as "en" | "hi") ?? "en"] ?? LABELS.en;
  const level = (lvl: string) => lvl && <span className="badge" style={{ marginLeft: 8 }}>{L.level[lvl] ?? lvl}</span>;
  return (
    <article className="stack" lang={r.language}>
      <h1>{r.title}</h1>
      <p>{r.intro}</p>

      <section className="card stack" aria-labelledby="r-strengths">
        <h2 id="r-strengths">{L.strengths}</h2>
        {r.strengths?.length ? r.strengths.map((s: any) => (
          <div key={s.skill_id} className="finding">
            <strong>{s.title}</strong>
            {s.clear && <span className="badge good" style={{ marginLeft: 8 }}>{L.clear}</span>}
            {level(s.evidence_level)}
            <div>{s.text}</div>
            {s.evidence_line && <div className="evidence">{L.evidence}: {s.evidence_line}</div>}
          </div>
        )) : <p className="muted">{L.none_s}</p>}
      </section>

      <section className="card stack" aria-labelledby="r-areas">
        <h2 id="r-areas">{L.areas}</h2>
        {r.areas_to_grow?.length ? r.areas_to_grow.map((a: any) => (
          <div key={a.skill_id} className="finding grow">
            <strong>{a.title}</strong>{level(a.evidence_level)}
            <div>{a.text}</div>
            {a.evidence_line && <div className="evidence">{L.evidence}: {a.evidence_line}</div>}
            {a.action_home && (
              <div className="grid two" style={{ marginTop: "0.5rem" }}>
                <div><strong>{L.home}:</strong> {a.action_home}</div>
                <div><strong>{L.school}:</strong> {a.action_school}</div>
              </div>
            )}
          </div>
        )) : <p className="muted">{L.none_a}</p>}
      </section>

      {r.patterns?.length > 0 && (
        <section className="card stack">
          <h2>{L.patterns}</h2>
          {r.patterns.map((p: any) => (
            <div key={p.type} className="finding pattern">
              <div>{p.text}{level(p.evidence_level)}</div>
              <div className="evidence">{L.evidence}: {p.evidence_line}</div>
            </div>
          ))}
        </section>
      )}

      {r.root_causes?.items?.length > 0 && (
        <section className="card stack">
          <h2>{L.causes}</h2>
          <p>{r.root_causes.summary}</p>
          <div className="table-wrap">
            <table className="data">
              <tbody>
                {r.root_causes.items.map((c: any) => (
                  <tr key={c.tag}><th scope="row">{c.label} ({c.count})</th><td>{c.suggestion}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {r.layers && (
        <section className="card">
          <h2>{L.skills}</h2>
          <div className="grid two">
            {r.layers.map((layer: any) => (
              <div key={layer.layer}>
                <h3>{layer.title}</h3>
                {layer.skills.map((s: any) => (
                  <div key={s.skill_id} className="skill-row">
                    <span>{s.title}{s.language_adjusted ? " *" : ""}</span>
                    <span className={`band-${s.band}`}>{s.band_label}</span>
                  </div>
                ))}
              </div>
            ))}
          </div>
          {r.layers.some((l: any) => l.skills.some((s: any) => s.language_adjusted)) && <p className="small muted">{L.adjusted}</p>}
        </section>
      )}

      {r.early_signals?.count > 0 && (
        <section className="card"><h2>{L.early}</h2><p>{r.early_signals.text}</p></section>
      )}
      {r.notes?.length > 0 && (
        <section className="card"><h2>{L.notes}</h2><ul>{r.notes.map((n: any, i: number) => <li key={i}>{n.text}</li>)}</ul></section>
      )}
      <p className="disclaimer">{r.disclaimer}</p>
      <p className="small muted">{L.version} {r.scoring_version}</p>
    </article>
  );
}
