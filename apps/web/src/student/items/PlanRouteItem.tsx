import { useRef, useState } from "react";
import { t, type PlanRouteContent } from "@sds/task-library";
import { Prompt, useItemTimer, type ItemProps } from "./common";

/** T14 Plan-Then-Solve: plan an errand route on a grid. Planning time is the delay before the first tap. */
export function PlanRouteItem({ item, lang, onSubmit, onIdle }: ItemProps) {
  const c = item.content as PlanRouteContent;
  const timer = useItemTimer(item.id, onIdle);
  const [route, setRoute] = useState<string[]>([]);
  const [restarts, setRestarts] = useState(0);
  const planMs = useRef<number | null>(null);
  const done = useRef(false);
  const at = new Map(c.places.map((p) => [`${p.pos[0]},${p.pos[1]}`, p]));

  const tapPlace = (id: string) => {
    if (route.includes(id)) return;
    if (planMs.current === null) planMs.current = Math.round(timer.finish().response_ms);
    timer.activity();
    setRoute((r) => [...r, id]);
  };
  const cells = [];
  for (let y = 0; y < c.grid; y++) {
    for (let x = 0; x < c.grid; x++) {
      const place = at.get(`${x},${y}`);
      const isHome = c.start[0] === x && c.start[1] === y;
      const order = place ? route.indexOf(place.id) : -1;
      cells.push(
        <button key={`${x}-${y}`} type="button" disabled={!place}
          className={`cell ${place ? "place" : ""} ${isHome ? "home" : ""} ${order >= 0 ? "visited" : ""}`}
          onClick={() => place && tapPlace(place.id)} aria-label={place ? t(lang, place.label_key) : isHome ? t(lang, "home") : undefined}>
          {isHome ? t(lang, "home") : place ? (order >= 0 ? `${order + 1}. ` : "") + t(lang, place.label_key) : ""}
        </button>,
      );
    }
  }
  return (
    <div>
      <Prompt text={t(lang, c.prompt_key)} lang={lang} />
      <div className="map" style={{ gridTemplateColumns: `repeat(${c.grid}, 1fr)`, maxWidth: 560 }}>{cells}</div>
      <div className="row" style={{ marginTop: "1rem" }}>
        <button type="button" className="btn secondary" disabled={!route.length}
          onClick={() => { timer.activity(); setRestarts((r) => r + 1); setRoute([]); }}>{t(lang, "reset")}</button>
        <span className="spacer" />
        <button type="button" className="btn big" disabled={route.length !== c.places.length}
          onClick={() => {
            if (done.current) return;
            done.current = true;
            onSubmit({ item, answer: route, timer, extra: { plan_ms: planMs.current ?? 0, restarts } });
          }}>{t(lang, "done")}</button>
      </div>
    </div>
  );
}
