import type { ChangeEntry } from "./types";

export type Clock = () => number;

/**
 * Per-item signal capture (FR-10): response time, first-interaction delay, answer changes, idle gaps and
 * app/tab switches, all on the device's monotonic clock with millisecond resolution.
 */
export class ItemTimer {
  readonly shownAt: number;
  readonly shownAtEpoch: number;
  private firstInteraction: number | null = null;
  private lastActivity: number;
  private idleTotal = 0;
  private idleMax = 0;
  private switchCount = 0;
  private answer: unknown = undefined;
  private changeLog: ChangeEntry[] = [];
  private hiddenSince: number | null = null;

  constructor(private readonly clock: Clock, epochNow: number = Date.now()) {
    this.shownAt = clock();
    this.shownAtEpoch = epochNow;
    this.lastActivity = this.shownAt;
  }

  private elapsed(): number {
    return this.clock() - this.shownAt;
  }

  /** Any touch, click or key press. Gaps longer than 2 s between activity count as idle time. */
  activity(): void {
    const now = this.clock();
    const gap = now - this.lastActivity;
    if (gap > 2000) {
      this.idleTotal += gap;
      this.idleMax = Math.max(this.idleMax, gap);
    }
    this.lastActivity = now;
    if (this.firstInteraction === null) this.firstInteraction = now - this.shownAt;
  }

  /** The student picked (or changed) an answer. Changes after the first pick are logged with direction. */
  select(answer: unknown): void {
    this.activity();
    if (this.answer !== undefined && JSON.stringify(this.answer) !== JSON.stringify(answer)) {
      this.changeLog.push({ from: this.answer, to: answer, at_ms: Math.round(this.elapsed()) });
    }
    this.answer = answer;
  }

  /** App or tab went to the background / came back. */
  visibility(hidden: boolean): void {
    const now = this.clock();
    if (hidden && this.hiddenSince === null) {
      this.hiddenSince = now;
      this.switchCount += 1;
    } else if (!hidden && this.hiddenSince !== null) {
      const gap = now - this.hiddenSince;
      this.idleTotal += gap;
      this.idleMax = Math.max(this.idleMax, gap);
      this.hiddenSince = null;
      this.lastActivity = now;
    }
  }

  idleNow(): number {
    return this.clock() - this.lastActivity;
  }

  finish(): {
    response_ms: number;
    first_click_ms: number | null;
    changes: number;
    change_log: ChangeEntry[];
    idle_ms: number;
    max_idle_ms: number;
    switches: number;
  } {
    const trailing = this.clock() - this.lastActivity;
    const idleTotal = this.idleTotal + (trailing > 2000 ? trailing : 0);
    const idleMax = Math.max(this.idleMax, trailing > 2000 ? trailing : 0);
    return {
      response_ms: Math.round(this.elapsed()),
      first_click_ms: this.firstInteraction === null ? null : Math.round(this.firstInteraction),
      changes: this.changeLog.length,
      change_log: this.changeLog,
      idle_ms: Math.round(idleTotal),
      max_idle_ms: Math.round(idleMax),
      switches: this.switchCount,
    };
  }
}
