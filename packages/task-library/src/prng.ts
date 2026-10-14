import type { Figure, StreamContent } from "./types";

/** mulberry32: bit-for-bit identical to backend/app/content/prng.py (see shared/test-vectors/prng.json). */
export function mulberry32(seed: number): () => number {
  let a = seed | 0;
  return () => {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export interface Stimulus {
  i: number;
  target: boolean;
  figure: Figure;
}

/** Expand a Focus Stream block into its stimuli. The server regenerates the same stream to score taps. */
export function streamSequence(content: Pick<StreamContent, "seed" | "duration_ms" | "isi_ms" | "target_rate" | "target" | "distractors">): Stimulus[] {
  const rnd = mulberry32(content.seed);
  const count = Math.floor(content.duration_ms / content.isi_ms);
  const out: Stimulus[] = [];
  for (let i = 0; i < count; i++) {
    if (rnd() < content.target_rate) {
      out.push({ i, target: true, figure: content.target });
    } else {
      const pick = Math.min(Math.floor(rnd() * content.distractors.length), content.distractors.length - 1);
      out.push({ i, target: false, figure: content.distractors[pick] });
    }
  }
  return out;
}

/** Deterministic, non-overlapping dot positions (0..1 box) for "which has more dots" items. */
export function dotLayout(count: number, seed: number, radius = 0.045): { x: number; y: number }[] {
  const rnd = mulberry32(seed);
  const dots: { x: number; y: number }[] = [];
  let guard = 0;
  while (dots.length < count && guard < count * 400) {
    guard++;
    const x = radius + rnd() * (1 - 2 * radius);
    const y = radius + rnd() * (1 - 2 * radius);
    if (dots.every((d) => (d.x - x) ** 2 + (d.y - y) ** 2 > (2.2 * radius) ** 2)) dots.push({ x, y });
  }
  while (dots.length < count) dots.push({ x: rnd(), y: rnd() });
  return dots;
}
