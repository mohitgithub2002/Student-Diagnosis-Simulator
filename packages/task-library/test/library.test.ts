import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import {
  ItemTimer, MemoryStorage, OfflineBuffer, SessionRunner, Staircase, alignErrors, answerFromText, checkAnswer,
  collectVoskResults, detectSpeech, dotLayout, figurePrims, framesFromLevels, initialTextMode, mulberry32,
  readAloudFromVad, readAloudFromWords, streamSequence, t, textFeatures, typedOutcome, voiceOutcome,
  type Bundle, type BundleItem, type ItemEvent, type Op, type TextResponseContent,
} from "../src";

const root = new URL("../../../shared/", import.meta.url);
const prng = JSON.parse(readFileSync(new URL("test-vectors/prng.json", root), "utf8"));
const stairs = JSON.parse(readFileSync(new URL("test-vectors/staircase.json", root), "utf8"));
const bundles: Record<string, Bundle> = JSON.parse(readFileSync(new URL("fixtures/bundles-11-14-en.json", root), "utf8"));

describe("shared vectors with the Python backend", () => {
  it("mulberry32 matches", () => {
    for (const c of prng.mulberry32) {
      const r = mulberry32(c.seed);
      expect(c.values.map(() => r())).toEqual(c.values);
    }
  });
  it("focus stream matches", () => {
    for (const c of prng.stream) {
      expect(streamSequence(c.content).map((s) => [s.target, s.figure.shape])).toEqual(c.expected);
    }
  });
  it("staircase matches", () => {
    for (const c of stairs.cases) {
      const sc = new Staircase(c.start);
      c.answers.forEach((a: boolean) => sc.record(a));
      expect(sc.state.history).toEqual(c.levels);
      expect(sc.level).toBe(c.final);
      expect(sc.state.reversals).toEqual(c.reversals);
      expect(sc.estimate()).toBe(c.estimate);
    }
  });
});

function fakeClock() {
  let now = 1000;
  const clock = () => now;
  return { clock, tick: (ms: number) => (now += ms) };
}

function correctAnswer(item: BundleItem): unknown {
  const c = item.content;
  if (c.kind === "sequence") return item.answer_key.sequence;
  if (c.kind === "estimate") return item.answer_key.value;
  if (c.kind === "plan_route") return item.answer_key.best_order;
  return item.answer_key.correct ?? null;
}

/** Drive a whole session the way a renderer would, answering everything correctly. */
function play(bundle: Bundle) {
  const events: ItemEvent[] = [];
  let id = 0;
  const runner = new SessionRunner(bundle, { onEvent: (e) => events.push(e), uuid: () => `id-${++id}` });
  const { clock, tick } = fakeClock();
  let guard = 0;
  while (runner.step.kind !== "session_done" && guard++ < 2000) {
    if (runner.step.kind === "task_intro") {
      runner.begin();
      continue;
    }
    const p = runner.step.presentation;
    const timer = new ItemTimer(clock, 1_700_000_000_000);
    tick(1500);
    const c = p.item.content;
    const base = { item: p.item, shownAtEpoch: timer.shownAtEpoch };
    if (c.kind === "passage_questions") {
      runner.submit({ ...base, answer: null, timing: timer.finish(), extra: { phase: "study" }, final: false });
      c.questions.forEach((q, i) => {
        runner.submit({ ...base, answer: p.item.answer_key.answers[q.id], timing: timer.finish(),
          extra: { qid: q.id, qtype: q.qtype }, final: i === c.questions.length - 1 });
        if (runner.pendingConfidence) runner.rate(3);
      });
    } else if (c.kind === "choice_menu") {
      runner.submit({ ...base, answer: "hard", timing: timer.finish() });
    } else if (c.kind === "bonus_offer") {
      runner.submit({ ...base, answer: "accept", timing: timer.finish() });
    } else {
      runner.submit({ ...base, answer: p.previous ? p.previous.answer : correctAnswer(p.item), timing: timer.finish() });
      if (runner.pendingConfidence) runner.rate(4);
    }
  }
  return { runner, events };
}

describe("session runner", () => {
  it("plays every session to the end and logs events with confidence", () => {
    for (const n of ["1", "2", "3", "4", "5", "6", "7"]) {
      const { runner, events } = play(bundles[n]);
      expect(runner.step.kind).toBe("session_done");
      expect(events.length).toBeGreaterThan(5);
      expect(new Set(events.map((e) => e.client_event_id)).size).toBe(events.length);
      expect(events.map((e) => e.seq)).toEqual(events.map((_, i) => i + 1));
      for (const e of events) {
        if (e.client_correct !== null && bundles[n].tasks.find((t) => t.task_id === e.task_id)?.confidence) {
          expect(e.confidence).not.toBeNull();
        }
      }
    }
  });

  it("raises the staircase level when answers are right", () => {
    const { events } = play(bundles["3"]);
    const t5 = events.filter((e) => e.task_id === "T5");
    const levels = t5.map((e) => Number(e.item_id.split("-L")[1].slice(0, 2)));
    expect(levels[levels.length - 1]).toBeGreaterThan(levels[0]);
  });

  it("T18 menu choices lead to the chosen puzzle, and the bonus offer to bonus puzzles", () => {
    const { events } = play(bundles["5"]);
    const t18 = events.filter((e) => e.task_id === "T18");
    expect(t18.filter((e) => e.condition === "t18_hard").length).toBe(6);
    expect(t18.filter((e) => e.condition === "bonus").length).toBe(3);
  });

  it("T15 ends with a review of the student's own answers", () => {
    const { events } = play(bundles["6"]);
    expect(events.filter((e) => e.task_id === "T15" && e.condition === "review").length).toBe(6);
  });

  it("T17 logs relaxed then pressure conditions", () => {
    const { events } = play(bundles["5"]);
    const conds = events.filter((e) => e.task_id === "T17").map((e) => e.condition);
    expect(conds.slice(0, 8).every((c) => c === "relaxed")).toBe(true);
    expect(conds.slice(8).every((c) => c === "pressure")).toBe(true);
  });

  it("offers a pause after three skips in a row", () => {
    const runner = new SessionRunner(bundles["1"], { onEvent: () => {}, uuid: () => Math.random().toString() });
    runner.begin();
    const { clock } = fakeClock();
    for (let i = 0; i < 3; i++) {
      const p = (runner.step as any).presentation;
      runner.submit({ item: p.item, answer: null, skipped: true, timing: new ItemTimer(clock).finish(), shownAtEpoch: 0 });
    }
    expect(runner.pauseOffered).toBe(true);
  });

  it("resumes at the first unfinished task", () => {
    const runner = new SessionRunner(bundles["2"], { onEvent: () => {}, uuid: () => "x", startTask: 2, seq: 40 });
    expect(runner.step.kind).toBe("task_intro");
    expect((runner.step as any).entry.task_id).toBe("T23");
    expect(runner.state).toEqual({ completedTasks: 2, seq: 40 });
  });
});

describe("signals", () => {
  it("captures first click, answer changes, idle gaps and app switches", () => {
    const { clock, tick } = fakeClock();
    const timer = new ItemTimer(clock);
    tick(800);
    timer.select("a");
    tick(5000);
    timer.select("b");
    timer.visibility(true);
    tick(3000);
    timer.visibility(false);
    tick(500);
    const f = timer.finish();
    expect(f.first_click_ms).toBe(800);
    expect(f.change_log).toEqual([{ from: "a", to: "b", at_ms: 5800 }]);
    expect(f.switches).toBe(1);
    expect(f.max_idle_ms).toBe(5000);
    expect(f.response_ms).toBe(9300);
  });
});

describe("checks", () => {
  it("agree with the answer keys in the bundles", () => {
    for (const b of Object.values(bundles)) {
      for (const task of b.tasks) {
        for (const item of task.items) {
          if (item.content.kind === "choice" && item.answer_key.correct !== undefined) {
            expect(checkAnswer(item, item.answer_key.correct)).toBe(true);
          }
        }
      }
    }
  });
});

describe("offline buffer", () => {
  it("keeps operations until they are sent, in order", async () => {
    const storage = new MemoryStorage();
    const buffer = new OfflineBuffer(storage);
    const ev = { client_event_id: "1" } as ItemEvent;
    await buffer.push({ type: "events", session: 1, events: [ev] });
    await buffer.push({ type: "events", session: 1, events: [{ ...ev, client_event_id: "2" }] });
    await buffer.push({ type: "complete", session: 1 });
    expect(await buffer.pending()).toBe(2); // the two event writes were batched
    let online = false;
    const sent: Op[] = [];
    const transport = { send: async (op: Op) => { if (!online) throw new Error("offline"); sent.push(op); } };
    expect(await buffer.flush(transport)).toBe(false);
    expect(await new OfflineBuffer(storage).pending()).toBe(2); // survives a restart
    online = true;
    expect(await buffer.flush(transport)).toBe(true);
    expect(sent.map((o) => o.type)).toEqual(["events", "complete"]);
  });
});

describe("text and voice features", () => {
  it("text features", () => {
    const f = textFeatures("First I would wait. Then I share my bottle because the bell rings.", ["bell", "bottle", "late"]);
    expect(f.word_count).toBe(13);
    expect(f.connectors).toBe(3);
    expect(f.keyword_share).toBeCloseTo(0.667, 2);
    expect(answerFromText("t11", "hello there", "text").map((x) => x.name)).toContain("t11.word_count");
  });
  it("voice activity detection finds speech and pauses", () => {
    const frames = [];
    for (let t = 0; t < 4000; t += 20) {
      const speaking = (t > 600 && t < 1800) || (t > 2600 && t < 3600);
      frames.push({ t, rms: speaking ? 0.2 : 0.005 });
    }
    const v = detectSpeech(frames);
    expect(v.speech_start_ms).toBe(620);
    expect(v.pause_count).toBe(1);
    expect(readAloudFromVad(50, v)[0].name).toBe("t7.wpm");
  });
  it("read-aloud error rate from recognised words", () => {
    expect(alignErrors(["the", "red", "kite"], ["the", "kite"])).toBe(1);
    const words = ["the", "red", "red", "kite", "flew"].map((w, i) => ({ word: w, start: i * 0.5, end: i * 0.5 + 0.4 }));
    const f = Object.fromEntries(readAloudFromWords("The red kite flew", words).map((x) => [x.name, x.value]));
    expect(f["t7.error_rate"]).toBe(0.25);
    expect(f["t7.self_corrections"]).toBeGreaterThan(0);
  });
});

describe("voice answers on web and Android", () => {
  const readAloud: TextResponseContent = { kind: "text_response", mode: "read_aloud", passage: "The red kite flew", word_count: 4, time_limit_s: 150 };
  const explain: TextResponseContent = { kind: "text_response", mode: "explain", prompt: "Why?", keywords: ["bell"], time_limit_s: 60 };
  const converse: TextResponseContent = { kind: "text_response", mode: "converse", prompt: "Tell me", time_limit_s: 60 };
  const speech = () => {
    const frames = [];
    for (let t = 0; t < 4000; t += 20) frames.push({ t, rms: (t > 600 && t < 1800) || (t > 2600 && t < 3600) ? 0.2 : 0.005 });
    return detectSpeech(frames);
  };
  const silence = detectSpeech(framesFromLevels(new Array(100).fill(0)));
  const byName = (rows: { name: string; value: number; channel: string }[]) => Object.fromEntries(rows.map((x) => [x.name, x]));

  it("collects Vosk results from strings and objects, skipping bad entries", () => {
    const out = collectVoskResults([
      JSON.stringify({ result: [{ word: "the", start: 0.5, end: 0.7, conf: 1 }, { word: "kite", start: 0.8, end: 1.1 }], text: "the kite" }),
      "{not json",
      { text: "" },
      { result: [{ word: "flew", start: 1.5, end: 1.9 }, { word: 7 as unknown as string, start: 2, end: 2.1 }], text: " flew " },
      JSON.stringify(null),
    ]);
    expect(out.words.map((w) => w.word)).toEqual(["the", "kite", "flew"]);
    expect(out.words[0]).toEqual({ word: "the", start: 0.5, end: 0.7 });
    expect(out.text).toBe("the kite flew");
  });
  it("turns evenly spaced levels into timestamped frames", () => {
    expect(framesFromLevels([0.1, 0.2, 0.3], 20)).toEqual([{ t: 0, rms: 0.1 }, { t: 20, rms: 0.2 }, { t: 40, rms: 0.3 }]);
  });
  it("chooses the starting mode from the task and voice availability", () => {
    expect(initialTextMode(readAloud, true)).toBe("voice");
    expect(initialTextMode(readAloud, false)).toBe("silent");
    expect(initialTextMode(explain, true)).toBe("choose");
    expect(initialTextMode(converse, false)).toBe("typed");
  });
  it("read aloud uses words when speech-to-text ran, energy timing otherwise", () => {
    const words = ["the", "red", "kite", "flew"].map((w, i) => ({ word: w, start: 0.6 + i * 0.4, end: 0.9 + i * 0.4 }));
    const withWords = voiceOutcome(readAloud, { vad: speech(), words, transcript: "the red kite flew" });
    expect(byName(withWords.features)["t7.error_rate"]).toMatchObject({ value: 0, channel: "voice" });
    expect(withWords.extra).toEqual({ mode: "voice", stt: true });
    expect(withWords.skipped).toBe(false);
    const energyOnly = voiceOutcome(readAloud, { vad: speech(), words: null, transcript: null });
    expect(byName(energyOnly.features)["t7.wpm"].channel).toBe("voice_vad");
    expect(byName(energyOnly.features)["t7.error_rate"]).toBeUndefined();
    expect(energyOnly.extra).toEqual({ mode: "voice", stt: false });
  });
  it("spoken answers keep timing with the transcript; silence counts as skipped", () => {
    const spoken = byName(voiceOutcome(explain, { vad: speech(), words: [], transcript: "first the bell rings then we go" }).features);
    expect(spoken["t11.keyword_share"]).toMatchObject({ value: 1, channel: "voice" });
    expect(spoken["t11.speech_start_ms"].value).toBe(620);
    expect(spoken["t11.pause_rate"]).toBeDefined();
    const energy = voiceOutcome(converse, { vad: speech(), words: null, transcript: null });
    expect(byName(energy.features)["t22.word_count"].channel).toBe("voice_vad");
    const quiet = voiceOutcome(converse, { vad: silence, words: null, transcript: null });
    expect(quiet.skipped).toBe(true);
    expect(quiet.features).toEqual([]);
  });
  it("typed answers use the text channel", () => {
    const typed = typedOutcome(explain, "The bell rings");
    expect(typed.features.every((f) => f.channel === "text" && f.name.startsWith("t11."))).toBe(true);
    expect(typed).toMatchObject({ extra: { mode: "typed" }, skipped: false });
    expect(typedOutcome(converse, "   ").skipped).toBe(true);
  });
});

describe("figures, dots and i18n", () => {
  it("draws every figure used by the bundles", () => {
    expect(figurePrims({ shape: "poly", cells: [[0, 0], [1, 0], [1, 1], [2, 1]], rotation: 90, count: 1, fill: "striped" })[0].attrs.d).toContain("M");
    expect(figurePrims({ shape: "star", rotation: 0, count: 3, fill: "empty" })).toHaveLength(3);
  });
  it("dot layouts are deterministic", () => {
    expect(dotLayout(20, 7)).toEqual(dotLayout(20, 7));
    expect(dotLayout(20, 7)).toHaveLength(20);
  });
  it("translates with fallbacks and variables", () => {
    expect(t("hi", "level", { n: 3 })).toBe("स्तर 3");
    expect(t("hinglish", "warmup.title")).toBe("Warm-up");
    expect(t("en", "t10.number_line", { target: 370 })).toContain("370");
  });
});
