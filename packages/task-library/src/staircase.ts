/**
 * Adaptive difficulty (FR-06): 10 levels, up one after 2 correct in a row, down one after a wrong answer.
 * The level estimate is the mean of the last 6 turning points. Mirrors backend/app/scoring/staircase.py;
 * shared/test-vectors/staircase.json keeps them in step.
 */
export const MIN_LEVEL = 1;
export const MAX_LEVEL = 10;

export interface StaircaseState {
  level: number;
  streak: number;
  lastDir: number;
  reversals: number[];
  history: number[];
}

export class Staircase {
  state: StaircaseState;

  constructor(start: number, state?: StaircaseState) {
    this.state = state ?? { level: start, streak: 0, lastDir: 0, reversals: [], history: [] };
  }

  get level(): number {
    return this.state.level;
  }

  /** Record an answer at the current level; returns the next level. */
  record(correct: boolean): number {
    const s = this.state;
    s.history.push(s.level);
    let move = 0;
    if (correct) {
      s.streak += 1;
      if (s.streak >= 2) {
        move = 1;
        s.streak = 0;
      }
    } else {
      s.streak = 0;
      move = -1;
    }
    if (move !== 0) {
      const next = Math.max(MIN_LEVEL, Math.min(MAX_LEVEL, s.level + move));
      if (next !== s.level) {
        if (s.lastDir !== 0 && move !== s.lastDir) s.reversals.push(s.level);
        s.lastDir = move;
        s.level = next;
      }
    }
    return s.level;
  }

  estimate(): number | null {
    const s = this.state;
    if (s.reversals.length >= 2) {
      const last = s.reversals.slice(-6);
      return round3(last.reduce((a, b) => a + b, 0) / last.length);
    }
    if (s.history.length === 0) return null;
    const tail = s.history.slice(Math.floor(s.history.length / 2));
    return round3(tail.reduce((a, b) => a + b, 0) / tail.length);
  }
}

function round3(x: number): number {
  return Math.round(x * 1000) / 1000;
}
