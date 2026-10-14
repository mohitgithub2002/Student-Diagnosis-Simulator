import { useEffect, useRef, useState } from "react";
import { ItemTimer, t, type AllocateContent, type BundleItem } from "@sds/task-library";
import { ChoiceItem } from "./ChoiceItem";
import { EstimateItem } from "./EstimateItem";
import { Prompt, type ItemProps } from "./common";

/**
 * T16 Time Budget: share a visible timer across three packs of mixed difficulty, then play. Logs each
 * puzzle plus a summary of planned vs actual time, unfinished puzzles and unused time.
 */
export function AllocateItem(props: ItemProps) {
  const { item, lang, onSubmit, aux = {} } = props;
  const c = item.content as AllocateContent;
  const total = c.total_s;
  const [planned, setPlanned] = useState<Record<string, number>>(
    Object.fromEntries(c.blocks.map((b) => [b.id, Math.round(total / c.blocks.length)])),
  );
  const [phase, setPhase] = useState<"plan" | "play">("plan");
  const [blockIdx, setBlockIdx] = useState(0);
  const [itemIdx, setItemIdx] = useState(0);
  const [now, setNow] = useState(0);
  const started = useRef(0);
  const blockStart = useRef(0);
  const actual = useRef<Record<string, number>>({});
  const answered = useRef(0);
  const summaryTimer = useRef(new ItemTimer(() => performance.now(), Date.now()));
  const finished = useRef(false);

  const used = Object.values(planned).reduce((a, b) => a + b, 0);
  const setBlock = (id: string, v: number) => {
    summaryTimer.current.activity();
    setPlanned((p) => ({ ...p, [id]: Math.max(0, Math.min(total, Math.round(v))) }));
  };

  const endRef = useRef<() => void>(() => undefined);
  useEffect(() => {
    if (phase !== "play") return;
    const id = window.setInterval(() => {
      const elapsed = (performance.now() - started.current) / 1000;
      setNow(elapsed);
      if (elapsed >= total) endRef.current();
    }, 250);
    return () => window.clearInterval(id);
  }, [phase, total]);

  const closeBlock = () => {
    const b = c.blocks[blockIdx];
    if (b) actual.current[b.id] = Math.round((actual.current[b.id] ?? 0) + (performance.now() - blockStart.current) / 1000);
  };

  const endAll = () => {
    if (finished.current) return;
    finished.current = true;
    closeBlock();
    const totalItems = c.blocks.reduce((a, b) => a + b.item_ids.length, 0);
    const elapsed = Math.min(total, (performance.now() - started.current) / 1000);
    onSubmit({
      item, answer: null, timer: summaryTimer.current, askConfidence: false,
      extra: { planned, actual: actual.current, unfinished: totalItems - answered.current, unused_s: Math.round(total - elapsed) },
    });
  };

  endRef.current = endAll;

  const nextBlock = () => {
    closeBlock();
    if (blockIdx + 1 >= c.blocks.length) {
      endAll();
      return;
    }
    blockStart.current = performance.now();
    setBlockIdx((i) => i + 1);
    setItemIdx(0);
  };

  if (phase === "plan") {
    return (
      <div className="stack">
        <Prompt text={t(lang, c.prompt_key, { total })} lang={lang} />
        {c.blocks.map((b) => (
          <label key={b.id} className="field">
            <span>{t(lang, b.label_key)} <span className="badge">{t(lang, `t16.${b.difficulty}`)}</span></span>
            <div className="row">
              <input type="range" min={0} max={total} step={5} value={planned[b.id]} style={{ flex: 1 }}
                onChange={(e) => setBlock(b.id, Number(e.target.value))} aria-label={t(lang, b.label_key)} />
              <strong style={{ minWidth: 90 }}>{t(lang, "t16.seconds", { s: planned[b.id] })}</strong>
            </div>
          </label>
        ))}
        <p className={used === total ? "muted" : "alert"}>{used} / {total}</p>
        <div className="row">
          <span className="spacer" />
          <button type="button" className="btn big" disabled={used !== total} onClick={() => {
            started.current = performance.now();
            blockStart.current = started.current;
            setPhase("play");
          }}>{t(lang, "start")}</button>
        </div>
      </div>
    );
  }

  const block = c.blocks[blockIdx];
  const refs = block?.item_ids.filter((id) => id in aux) ?? [];
  const sub: BundleItem | undefined = aux[refs[itemIdx]];
  const blockElapsed = (performance.now() - blockStart.current) / 1000;
  const subSubmit: ItemProps["onSubmit"] = (d) => {
    answered.current += 1;
    onSubmit({ ...d, condition: `t16:${block.id}`, final: false, askConfidence: false });
    if (itemIdx + 1 < refs.length) setItemIdx((i) => i + 1);
    else nextBlock();
  };
  return (
    <div>
      <div className="row" style={{ marginBottom: "0.75rem" }}>
        <strong>{block && t(lang, block.label_key)}</strong>
        <span className="badge">{t(lang, "time_left", { s: Math.max(0, Math.ceil(total - now)) })}</span>
        <span className="badge warn">{Math.round(blockElapsed)} / {planned[block?.id] ?? 0}s</span>
        <span className="spacer" />
        <button type="button" className="btn secondary" onClick={nextBlock}>{t(lang, "t16.next_pack")}</button>
      </div>
      {sub && (sub.content.kind === "estimate"
        ? <EstimateItem key={sub.id} {...props} item={sub} embedded onSubmit={subSubmit} />
        : <ChoiceItem key={sub.id} {...props} item={sub} taskId="T16" settings={{}} embedded onSubmit={subSubmit} />)}
    </div>
  );
}
