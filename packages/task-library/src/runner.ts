import { checkAnswer } from "./checks";
import type { ItemTimer } from "./signals";
import { Staircase } from "./staircase";
import type { BundleItem, Bundle, ItemEvent, TaskEntry } from "./types";

/**
 * Headless session runner shared by the web and Android apps. It decides what to show next (including the
 * adaptive staircase), turns renderer results into logged events, asks the T13 confidence question after
 * scored items, and offers a pause when the student seems stuck or idle. Renderers only draw items.
 */

export interface Presentation {
  key: string;
  taskIndex: number;
  entry: TaskEntry;
  item: BundleItem;
  condition: string;
  phase: string;
  settings: Record<string, any>;
  index: number;
  total: number;
  previous?: ItemEvent;
}

export interface Draft {
  item: BundleItem;
  answer: unknown;
  timing: ReturnType<ItemTimer["finish"]>;
  shownAtEpoch: number;
  skipped?: boolean;
  extra?: Record<string, unknown>;
  retries?: number;
  condition?: string;
  /** False when the renderer will submit more drafts for the same presentation (passages, packs). */
  final?: boolean;
  askConfidence?: boolean;
}

export type Step =
  | { kind: "task_intro"; taskIndex: number; entry: TaskEntry }
  | { kind: "present"; presentation: Presentation }
  | { kind: "session_done" };

type Pending = Omit<Presentation, "key" | "taskIndex" | "entry" | "index" | "total">;

interface TaskPlayer {
  total: number;
  next(): Pending | null;
  report(p: Presentation, ev: ItemEvent): void;
}

class ListPlayer implements TaskPlayer {
  private i = 0;
  constructor(private items: Pending[]) {}
  get total() {
    return this.items.length;
  }
  next() {
    return this.i < this.items.length ? this.items[this.i++] : null;
  }
  report() {}
  push(p: Pending) {
    this.items.push(p);
  }
}

class StaircasePlayer implements TaskPlayer {
  private sc: Staircase;
  private used = new Set<string>();
  private shown = 0;
  constructor(private pools: Record<string, BundleItem[]>, start: number, readonly total: number,
    private base: Omit<Pending, "item">) {
    this.sc = new Staircase(start);
  }
  next(): Pending | null {
    if (this.shown >= this.total) return null;
    const levels = Object.keys(this.pools).map(Number).sort((a, b) => a - b);
    const byDistance = [...levels].sort((a, b) => Math.abs(a - this.sc.level) - Math.abs(b - this.sc.level));
    for (const lvl of byDistance) {
      const item = (this.pools[String(lvl)] ?? []).find((it) => !this.used.has(it.id));
      if (item) {
        this.used.add(item.id);
        this.shown++;
        return { ...this.base, item };
      }
    }
    return null;
  }
  report(_p: Presentation, ev: ItemEvent) {
    if (ev.client_correct !== null) this.sc.record(Boolean(ev.client_correct));
  }
  estimate() {
    return this.sc.estimate();
  }
}

class ChainPlayer implements TaskPlayer {
  private k = 0;
  constructor(private parts: TaskPlayer[]) {}
  get total() {
    return this.parts.reduce((a, p) => a + p.total, 0);
  }
  next(): Pending | null {
    while (this.k < this.parts.length) {
      const n = this.parts[this.k].next();
      if (n) return n;
      this.k++;
    }
    return null;
  }
  report(p: Presentation, ev: ItemEvent) {
    this.parts[Math.min(this.k, this.parts.length - 1)].report(p, ev);
  }
}

/** T15: after the first pass, the student reviews their own answers and may change them. */
class ReviewPlayer implements TaskPlayer {
  private first: ListPlayer;
  private review: Pending[] = [];
  private answers = new Map<string, ItemEvent>();
  private reviewing = false;
  private r = 0;
  constructor(private items: BundleItem[], private settings: Record<string, any>) {
    this.first = new ListPlayer(items.map((item) => ({ item, condition: "", phase: "first", settings })));
  }
  get total() {
    return this.items.length * 2;
  }
  next(): Pending | null {
    if (!this.reviewing) {
      const n = this.first.next();
      if (n) return n;
      this.reviewing = true;
      this.review = this.items
        .filter((it) => this.answers.has(it.id))
        .map((it) => ({ item: it, condition: "review", phase: "review", settings: this.settings, previous: this.answers.get(it.id) }));
    }
    return this.r < this.review.length ? this.review[this.r++] : null;
  }
  report(p: Presentation, ev: ItemEvent) {
    if (p.phase === "first") this.answers.set(p.item.id, ev);
  }
}

/** T18: a menu choice leads to the chosen puzzle; the bonus offer leads to optional bonus puzzles. */
class MenuPlayer implements TaskPlayer {
  private queue: Pending[];
  constructor(entry: TaskEntry, private aux: Record<string, BundleItem>) {
    this.queue = entry.items.map((item) => ({ item, condition: item.content.kind === "bonus_offer" ? "bonus_offer" : "menu",
      phase: "menu", settings: entry.settings }));
  }
  get total() {
    return this.queue.length * 2;
  }
  next() {
    return this.queue.shift() ?? null;
  }
  report(p: Presentation, ev: ItemEvent) {
    const c = p.item.content;
    if (c.kind === "choice_menu") {
      const ref = ev.answer === "hard" ? c.hard_ref : c.easy_ref;
      const item = this.aux[ref];
      if (item) this.queue.unshift({ item, condition: `t18_${ev.answer === "hard" ? "hard" : "easy"}`, phase: "solve", settings: p.settings });
    } else if (c.kind === "bonus_offer" && ev.answer === "accept") {
      const bonus = c.refs.map((ref) => this.aux[ref]).filter(Boolean)
        .map((item) => ({ item, condition: "bonus", phase: "bonus", settings: p.settings }));
      this.queue.unshift(...bonus);
    }
  }
}

function playerFor(entry: TaskEntry, aux: Record<string, BundleItem>): TaskPlayer {
  const s = entry.settings ?? {};
  switch (entry.task_id) {
    case "T1": {
      const pools = entry.pools as Record<string, Record<string, BundleItem[]>>;
      const per = entry.items_per_run as Record<string, number>;
      return new ChainPlayer(["forward", "backward"].map((dir) =>
        new StaircasePlayer(pools[dir], entry.start_level ?? 3, per[dir] ?? 8, { condition: "", phase: dir, settings: s })));
    }
    case "T2":
      return new ListPlayer(entry.items.map((item) => ({ item, condition: s.phase ?? "immediate", phase: s.phase ?? "immediate", settings: s })));
    case "T15":
      return new ReviewPlayer(entry.items, s);
    case "T17":
      return new ListPlayer(entry.items.map((item) => {
        const condition = (item.content as { condition?: string }).condition ?? "relaxed";
        return { item, condition, phase: condition, settings: { ...s, pressure: condition === "pressure" } };
      }));
    case "T18":
      return new MenuPlayer(entry, aux);
    default:
      if (entry.adaptive && entry.pools) {
        return new StaircasePlayer(entry.pools as Record<string, BundleItem[]>, entry.start_level ?? 3,
          Number(entry.items_per_run ?? 14), { condition: "", phase: "", settings: s });
      }
      return new ListPlayer(entry.items.map((item) => ({ item, condition: "", phase: "", settings: s })));
  }
}

export interface RunnerOptions {
  onEvent: (ev: ItemEvent) => void;
  uuid: () => string;
  startTask?: number;
  seq?: number;
  idlePauseMs?: number;
  skipsBeforePause?: number;
}

export interface RunnerState {
  completedTasks: number;
  seq: number;
}

export class SessionRunner {
  step: Step;
  pendingConfidence: ItemEvent | null = null;
  pauseOffered = false;
  private taskIndex: number;
  private player: TaskPlayer | null = null;
  private current: Presentation | null = null;
  private pendingFinal = false;
  private seq: number;
  private shownInTask = 0;
  private consecutiveSkips = 0;
  private listeners = new Set<() => void>();

  constructor(readonly bundle: Bundle, private opts: RunnerOptions) {
    this.taskIndex = opts.startTask ?? 0;
    this.seq = opts.seq ?? 0;
    this.step = this.introOrDone();
  }

  subscribe(fn: () => void): () => void {
    this.listeners.add(fn);
    return () => this.listeners.delete(fn);
  }

  private changed() {
    this.listeners.forEach((fn) => fn());
  }

  get state(): RunnerState {
    return { completedTasks: this.taskIndex, seq: this.seq };
  }

  get progress() {
    return {
      taskIndex: this.taskIndex,
      tasks: this.bundle.tasks.length,
      item: this.shownInTask,
      items: this.player?.total ?? 0,
    };
  }

  private introOrDone(): Step {
    const entry = this.bundle.tasks[this.taskIndex];
    if (!entry) return { kind: "session_done" };
    return { kind: "task_intro", taskIndex: this.taskIndex, entry };
  }

  /** Leave the task intro screen and show the first item. */
  begin(): void {
    if (this.step.kind !== "task_intro") return;
    this.player = playerFor(this.step.entry, this.bundle.aux_items);
    this.shownInTask = 0;
    this.advance();
  }

  private advance(): void {
    const entry = this.bundle.tasks[this.taskIndex];
    const next = this.player?.next() ?? null;
    if (!next) {
      this.taskIndex++;
      this.player = null;
      this.current = null;
      this.step = this.introOrDone();
    } else {
      this.shownInTask++;
      this.current = {
        ...next,
        key: `${this.taskIndex}:${this.shownInTask}:${next.item.id}:${next.condition}`,
        taskIndex: this.taskIndex,
        entry,
        index: this.shownInTask,
        total: Math.max(this.player!.total, this.shownInTask),
      };
      this.step = { kind: "present", presentation: this.current };
    }
    this.changed();
  }

  /** A renderer finished an item (or one part of a multi-part item). */
  submit(draft: Draft): ItemEvent {
    const p = this.current;
    if (!p) throw new Error("nothing is being presented");
    const extra = draft.extra ?? {};
    const skipped = Boolean(draft.skipped);
    const correct = checkAnswer(draft.item, draft.answer, extra, skipped);
    const ev: ItemEvent = {
      client_event_id: this.opts.uuid(),
      item_id: draft.item.id,
      task_id: p.entry.task_id,
      seq: ++this.seq,
      shown_at_ms: draft.shownAtEpoch,
      response_ms: draft.timing.response_ms,
      first_click_ms: draft.timing.first_click_ms,
      answer: draft.answer ?? null,
      client_correct: correct,
      changes: draft.timing.changes,
      change_log: draft.timing.change_log,
      skipped,
      retries: draft.retries ?? 0,
      confidence: null,
      idle_ms: draft.timing.idle_ms,
      max_idle_ms: draft.timing.max_idle_ms,
      switches: draft.timing.switches,
      language: draft.item.language,
      condition: draft.condition ?? p.condition,
      extra,
    };
    this.consecutiveSkips = skipped ? this.consecutiveSkips + 1 : 0;
    if (this.consecutiveSkips >= (this.opts.skipsBeforePause ?? 3)) this.pauseOffered = true;
    const final = draft.final ?? true;
    const ask = draft.askConfidence ?? (p.entry.confidence && correct !== null && !skipped);
    if (ask) {
      this.pendingConfidence = ev;
      this.pendingFinal = final;
      this.changed();
      return ev;
    }
    this.emit(ev, final);
    return ev;
  }

  /** The T13 rating for the pending item (1 = just guessing .. 4 = very sure). */
  rate(confidence: number): void {
    const ev = this.pendingConfidence;
    if (!ev) return;
    ev.confidence = Math.max(1, Math.min(4, Math.round(confidence)));
    this.pendingConfidence = null;
    this.emit(ev, this.pendingFinal);
  }

  private emit(ev: ItemEvent, final: boolean): void {
    this.opts.onEvent(ev);
    if (final && this.current) {
      this.player?.report(this.current, ev);
      this.advance();
    } else {
      this.changed();
    }
  }

  /** Renderers call this while waiting for input; a long idle gap offers a pause instead of pushing on. */
  idle(ms: number): void {
    if (!this.pauseOffered && ms >= (this.opts.idlePauseMs ?? 45000)) {
      this.pauseOffered = true;
      this.changed();
    }
  }

  dismissPause(): void {
    this.pauseOffered = false;
    this.consecutiveSkips = 0;
    this.changed();
  }
}
