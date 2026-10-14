import type { BundleItem, PlanRouteContent } from "./types";

/** Device-side correctness, used only to drive the staircase. The server re-checks every answer. */
export function routeCost(content: PlanRouteContent, order: string[]): number | null {
  const pos = new Map(content.places.map((p) => [p.id, p.pos]));
  if (order.length !== pos.size || !order.every((id) => pos.has(id))) return null;
  let cost = 0;
  let cur = content.start;
  for (const id of order) {
    const next = pos.get(id)!;
    cost += Math.abs(next[0] - cur[0]) + Math.abs(next[1] - cur[1]);
    cur = next;
  }
  return cost;
}

export function checkAnswer(item: BundleItem, answer: unknown, extra: Record<string, unknown> = {}, skipped = false): boolean | null {
  const c = item.content;
  const key = item.answer_key;
  switch (c.kind) {
    case "passage_questions": {
      const qid = extra.qid as string | undefined;
      if (!qid) return null;
      const expected = key.answers?.[qid];
      if (expected === undefined) return null;
      return skipped ? false : answer === expected;
    }
    case "sequence":
      if (skipped || !Array.isArray(answer)) return false;
      return answer.length === key.sequence.length && answer.every((a, i) => String(a) === String(key.sequence[i]));
    case "choice":
      if (key.correct === undefined) return null;
      return skipped || answer == null ? false : String(answer) === String(key.correct);
    case "estimate": {
      if (skipped || answer == null) return false;
      const v = Number(answer);
      if (!Number.isFinite(v)) return false;
      return Math.abs(v - key.value) <= (key.tolerance ?? 0.05) * (c.max - c.min);
    }
    case "plan_route": {
      if (skipped || !Array.isArray(answer)) return false;
      const cost = routeCost(c, answer.map(String));
      return cost !== null && cost <= key.best_cost * (1 + (key.tolerance ?? 0.1));
    }
    default:
      return null;
  }
}
