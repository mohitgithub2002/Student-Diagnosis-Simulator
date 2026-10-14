import { Link, Route, Routes } from "react-router-dom";
import { AuditLog, ItemBank, Quality, ReviewQueue, ReviewReport, ScoringConfigs } from "./admin/AdminPages";
import { Logo, SvgDefs } from "./components/ui";
import { ConsentPage } from "./consent/ConsentPage";
import { ParentHome, ParentLogin, ParentReport } from "./parent/ParentPages";
import { ClassPage, SchoolDashboard, SharedReport, SharedReports, StaffLogin } from "./school/SchoolPages";
import { Play } from "./student/Play";
import { StudentHome, StudentLogin, StudentReport, Warmup } from "./student/StudentPages";

function Landing() {
  const tiles = [
    { to: "/play", title: "I'm a student", text: "Sign in with your class code and PIN to play." },
    { to: "/parent", title: "I'm a parent", text: "Give consent, see progress and read your child's report." },
    { to: "/school", title: "School staff", text: "Enrol classes, track consent and completion, schedule sessions." },
    { to: "/admin", title: "Internal review", text: "Review flagged reports, manage the item bank and scoring." },
  ];
  return (
    <>
      <header className="topbar"><div className="inner"><span className="brand"><Logo /> Student Diagnostic Simulator</span></div></header>
      <main className="page stack">
        <h1>How does this student think, learn and handle pressure?</h1>
        <p className="muted" style={{ maxWidth: 680 }}>
          Seven short, game-like sessions profile 24 skills across thinking, learning foundations, self-awareness, emotions
          and habits, then give parents and students a strengths-first, evidence-backed report. It is a screening profile,
          not a clinical assessment, and it never ranks students.
        </p>
        <div className="grid two">
          {tiles.map((t) => (
            <Link key={t.to} to={t.to} className="card" style={{ textDecoration: "none", color: "inherit" }}>
              <h2>{t.title}</h2>
              <p className="muted" style={{ margin: 0 }}>{t.text}</p>
            </Link>
          ))}
        </div>
      </main>
    </>
  );
}

function Game({ children }: { children: React.ReactNode }) {
  return <div className="game">{children}</div>;
}

export function App() {
  return (
    <>
      <SvgDefs />
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/play" element={<Game><StudentLogin /></Game>} />
        <Route path="/play/warmup" element={<Game><Warmup /></Game>} />
        <Route path="/play/home" element={<Game><StudentHome /></Game>} />
        <Route path="/play/session/:number" element={<Game><Play /></Game>} />
        <Route path="/play/report" element={<Game><StudentReport /></Game>} />
        <Route path="/consent/:token" element={<ConsentPage />} />
        <Route path="/parent" element={<ParentLogin />} />
        <Route path="/parent/home" element={<ParentHome />} />
        <Route path="/parent/report/:studentId" element={<ParentReport />} />
        <Route path="/school" element={<StaffLogin area="school" />} />
        <Route path="/school/dashboard" element={<SchoolDashboard />} />
        <Route path="/school/class/:classId" element={<ClassPage />} />
        <Route path="/school/reports" element={<SharedReports />} />
        <Route path="/school/reports/:studentId" element={<SharedReport />} />
        <Route path="/admin" element={<StaffLogin area="admin" />} />
        <Route path="/admin/review" element={<ReviewQueue />} />
        <Route path="/admin/review/:reportId" element={<ReviewReport />} />
        <Route path="/admin/items" element={<ItemBank />} />
        <Route path="/admin/scoring" element={<ScoringConfigs />} />
        <Route path="/admin/quality" element={<Quality />} />
        <Route path="/admin/audit" element={<AuditLog />} />
        <Route path="*" element={<div className="page"><h1>Page not found</h1><Link to="/">Home</Link></div>} />
      </Routes>
    </>
  );
}
