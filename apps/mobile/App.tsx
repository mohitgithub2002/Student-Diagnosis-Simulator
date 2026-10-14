import { StatusBar } from "expo-status-bar";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Modal, Pressable, SafeAreaView, ScrollView, Text, TextInput, View } from "react-native";
import {
  ApiError, LANGUAGE_NAMES, OfflineBuffer, SessionRunner, t, type Bundle, type FeatureRow, type Lang,
} from "@sds/task-library";
import { ItemView, type Submit } from "./src/items/Items";
import { deviceStorage, makeClient, speak, uuid } from "./src/platform";
import { Btn, C, Card, H1, P, s } from "./src/ui";

type Student = { id: string; name: string; language: Lang; age_band: string };
type Screen = { name: "login" } | { name: "warmup" } | { name: "home" } | { name: "play"; n: number } | { name: "report" };

/** Android shell: the same session runner, buffer and API client as the web app, with native renderers. */
export default function App() {
  const [screen, setScreen] = useState<Screen>({ name: "login" });
  const [token, setToken] = useState<string | null>(null);
  const [student, setStudent] = useState<Student | null>(null);
  const api = useMemo(() => makeClient(token), [token]);
  const lang = student?.language ?? "en";
  return (
    <SafeAreaView style={s.screen}>
      <StatusBar style="dark" />
      {screen.name === "login" && <Login onDone={(tk, st) => { setToken(tk); setStudent(st); setScreen({ name: "warmup" }); }} />}
      {screen.name === "warmup" && student && (
        <Warmup lang={lang} onDone={async (l) => {
          await api.warmup(l, false, true).catch(() => undefined);
          setStudent({ ...student, language: l });
          setScreen({ name: "home" });
        }} />
      )}
      {screen.name === "home" && student && <Home api={api} student={student} go={setScreen} />}
      {screen.name === "play" && student && <Play api={api} n={screen.n} student={student} exit={() => setScreen({ name: "home" })} />}
      {screen.name === "report" && <Report api={api} back={() => setScreen({ name: "home" })} lang={lang} />}
    </SafeAreaView>
  );
}

function Login({ onDone }: { onDone: (token: string, s: Student) => void }) {
  const [code, setCode] = useState("");
  const [pin, setPin] = useState("");
  const [error, setError] = useState<string | null>(null);
  return (
    <ScrollView contentContainerStyle={[s.scroll, { paddingTop: 60 }]}>
      <H1>{t("en", "login.title")}</H1>
      <Card>
        <P>{t("en", "login.class_code")}</P>
        <TextInput style={s.input} autoCapitalize="characters" value={code} onChangeText={(v) => setCode(v.toUpperCase())} />
        <P>{t("en", "login.pin")}</P>
        <TextInput style={s.input} keyboardType="number-pad" secureTextEntry maxLength={4} value={pin} onChangeText={(v) => setPin(v.replace(/\D/g, ""))} />
        {error && <Text style={{ color: C.danger }}>{error}</Text>}
        <Btn big title={t("en", "login.go")} onPress={async () => {
          try {
            const res = await makeClient(null).studentLogin(code.trim(), pin);
            onDone(res.token, res.student as Student);
          } catch (e) {
            const d = e instanceof ApiError ? String(e.detail) : "Network error";
            setError(d === "consent_required" ? "Your parent has not given consent yet." : d);
          }
        }} />
      </Card>
    </ScrollView>
  );
}

function Warmup({ lang, onDone }: { lang: Lang; onDone: (l: Lang) => void }) {
  const [l, setL] = useState<Lang>(lang);
  return (
    <ScrollView contentContainerStyle={s.scroll}>
      <H1>{t(l, "warmup.title")}</H1>
      <Card>
        <P big>{t(l, "warmup.language")}</P>
        <View style={s.row}>
          {(["en", "hi", "hinglish"] as Lang[]).map((x) => <Btn key={x} kind={x === l ? "primary" : "secondary"} title={LANGUAGE_NAMES[x]} onPress={() => setL(x)} />)}
        </View>
      </Card>
      <Card>
        <P big>{t(l, "warmup.audio")}</P>
        <Btn kind="secondary" title={t(l, "warmup.play_sound")} onPress={() => speak(t(l, "lets_go"), l)} />
      </Card>
      <Btn big title={t(l, "continue")} onPress={() => onDone(l)} />
    </ScrollView>
  );
}

function Home({ api, student, go }: { api: ReturnType<typeof makeClient>; student: Student; go: (s: Screen) => void }) {
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { api.home().then(setData, (e) => setError(String(e.message))); }, [api]);
  const lang = student.language;
  return (
    <ScrollView contentContainerStyle={s.scroll}>
      <H1>{t(lang, "home.hello", { name: student.name.split(" ")[0] })}</H1>
      {error && <Text style={{ color: C.danger }}>{error}</Text>}
      {data?.report_ready && <Btn big title={t(lang, "home.report")} onPress={() => go({ name: "report" })} />}
      <P big>{t(lang, "home.levels")}</P>
      <View style={[s.row, { gap: 12 }]}>
        {data?.sessions.map((x: any) => {
          const st = x.availability.state;
          const open = st === "available" || st === "in_progress";
          return (
            <Pressable key={x.number} disabled={!open} onPress={() => go({ name: "play", n: x.number })}
              style={[s.card, { width: 100, alignItems: "center", borderColor: st === "completed" ? C.good : open ? C.brand2 : C.line, borderWidth: 2 }]}>
              <Text style={{ fontSize: 30, fontWeight: "800", color: C.brand }}>{x.number}</Text>
              <Text style={{ fontSize: 12, color: C.muted, textAlign: "center" }}>{t(lang, st === "upcoming" ? "locked" : st)}</Text>
            </Pressable>
          );
        })}
      </View>
    </ScrollView>
  );
}

function Play({ api, n, student, exit }: { api: ReturnType<typeof makeClient>; n: number; student: Student; exit: () => void }) {
  const buffer = useMemo(() => new OfflineBuffer(deviceStorage, `sds.queue.${student.id}`), [student.id]);
  const [runner, setRunner] = useState<SessionRunner | null>(null);
  const [bundle, setBundle] = useState<Bundle | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [, setTick] = useState(0);
  const lastTask = useRef(-1);
  const lang = (bundle?.language ?? student.language) as Lang;

  useEffect(() => {
    api.startSession(n, "android").then((res) => {
      setBundle(res.bundle);
      const r = new SessionRunner(res.bundle, {
        onEvent: (ev) => { void buffer.push({ type: "events", session: n, events: [ev] }).then(() => buffer.flush(api)); },
        uuid, startTask: res.resume_state?.completedTasks ?? 0, seq: res.resume_state?.seq ?? 0,
      });
      r.subscribe(() => setTick((x) => x + 1));
      setRunner(r);
    }, (e) => setError(e instanceof ApiError ? String(e.detail) : "Network error"));
    const id = setInterval(() => void buffer.flush(api), 10000);
    return () => clearInterval(id);
  }, [n]); // eslint-disable-line

  useEffect(() => {
    if (!runner) return;
    if (runner.state.completedTasks !== lastTask.current) {
      lastTask.current = runner.state.completedTasks;
      const op = runner.step.kind === "session_done" ? { type: "complete" as const, session: n }
        : { type: "state" as const, session: n, state: { ...runner.state } };
      void buffer.push(op).then(() => buffer.flush(api));
    }
  });

  const onSubmit: Submit = useCallback(({ timer, ...rest }) => runner?.submit({ ...rest, timing: timer.finish(), shownAtEpoch: timer.shownAtEpoch }), [runner]);
  const onFeatures = useCallback((rows: FeatureRow[]) => { void buffer.push({ type: "features", session: n, features: rows }).then(() => buffer.flush(api)); }, [buffer, api, n]);

  if (error) return <View style={s.scroll}><P>{error}</P><Btn title={t(lang, "back")} onPress={exit} /></View>;
  if (!runner || !bundle) return <View style={s.scroll}><P muted>{t(lang, "loading")}</P></View>;
  const step = runner.step;
  return (
    <ScrollView contentContainerStyle={s.scroll} keyboardShouldPersistTaps="handled">
      <P muted>{t(lang, "level", { n })} · {t(lang, "of", { a: runner.progress.taskIndex + 1, b: runner.progress.tasks })}</P>
      <Card>
        {step.kind === "task_intro" && (
          <View style={{ gap: 14, alignItems: "center" }}>
            <H1>{step.entry.title}</H1>
            <Pressable onPress={() => speak(step.entry.instructions, lang)}><P>{step.entry.instructions} 🔊</P></Pressable>
            <Btn big title={t(lang, "lets_go")} onPress={() => runner.begin()} />
          </View>
        )}
        {step.kind === "present" && (
          <ItemView key={step.presentation.key} p={step.presentation} lang={lang} aux={bundle.aux_items} onSubmit={onSubmit}
            onIdle={(ms) => runner.idle(ms)} onFeatures={onFeatures} />
        )}
        {step.kind === "session_done" && (
          <View style={{ gap: 14, alignItems: "center" }}>
            <Text style={{ fontSize: 48, color: C.accent }}>★★★</Text>
            <H1>{t(lang, "session_complete")}</H1>
            <Btn big title={t(lang, "continue")} onPress={exit} />
          </View>
        )}
      </Card>
      <Modal transparent visible={Boolean(runner.pendingConfidence)} animationType="fade">
        <View style={{ flex: 1, backgroundColor: "rgba(23,50,77,0.45)", justifyContent: "center", padding: 16 }}>
          <Card>
            <P big>{t(lang, "how_sure")}</P>
            {[1, 2, 3, 4].map((c) => <Btn key={c} kind="secondary" title={`${"▮".repeat(c)}  ${t(lang, `conf_${c}`)}`} onPress={() => runner.rate(c)} />)}
          </Card>
        </View>
      </Modal>
      <Modal transparent visible={runner.pauseOffered && !runner.pendingConfidence} animationType="fade">
        <View style={{ flex: 1, backgroundColor: "rgba(23,50,77,0.45)", justifyContent: "center", padding: 16 }}>
          <Card>
            <P big>{t(lang, "pause_title")}</P>
            <P>{t(lang, "pause_text")}</P>
            <Btn kind="secondary" title={t(lang, "take_break")} onPress={() => { void buffer.push({ type: "state", session: n, state: { ...runner.state } }).then(() => buffer.flush(api)); exit(); }} />
            <Btn title={t(lang, "keep_going")} onPress={() => runner.dismissPause()} />
          </Card>
        </View>
      </Modal>
    </ScrollView>
  );
}

function Report({ api, back, lang }: { api: ReturnType<typeof makeClient>; back: () => void; lang: Lang }) {
  const [r, setR] = useState<any>(null);
  useEffect(() => { api.studentReport().then((x) => setR(x.content), () => setR(null)); }, [api]);
  if (!r) return <View style={s.scroll}><P muted>{t(lang, "loading")}</P><Btn title={t(lang, "back")} onPress={back} /></View>;
  return (
    <ScrollView contentContainerStyle={s.scroll}>
      <H1>{r.title}</H1>
      <P>{r.intro}</P>
      <Card><P big>{t(r.language, "report.strengths")}</P>{r.strengths.map((x: any) => <P key={x.skill_id}>• {x.title}: {x.text}</P>)}</Card>
      <Card><P big>{t(r.language, "report.grow")}</P>{r.areas_to_grow.map((x: any) => <P key={x.skill_id}>• {x.title}: {x.text}</P>)}</Card>
      {r.action && <Card><P big>{t(r.language, "report.action")}</P><P>{r.action}</P></Card>}
      <P muted>{r.disclaimer}</P>
      <Btn kind="secondary" title={t(lang, "back")} onPress={back} />
    </ScrollView>
  );
}
