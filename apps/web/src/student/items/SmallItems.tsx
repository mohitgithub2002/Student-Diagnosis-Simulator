import { useRef, useState } from "react";
import { t, type ChoiceMenuContent, type SurveyContent } from "@sds/task-library";
import { OptionButton, Prompt, useItemTimer, type ItemProps } from "./common";

/** T18 Choice Menu and the optional bonus offer. */
export function MenuItem({ item, lang, onSubmit, onIdle }: ItemProps) {
  const timer = useItemTimer(item.id, onIdle);
  const done = useRef(false);
  const pick = (answer: string) => {
    if (done.current) return;
    done.current = true;
    timer.select(answer);
    onSubmit({ item, answer, timer, askConfidence: false });
  };
  if (item.content.kind === "bonus_offer") {
    return (
      <div className="stack center">
        <Prompt text={t(lang, item.content.prompt_key)} lang={lang} />
        <div className="row" style={{ justifyContent: "center" }}>
          <button type="button" className="btn big" onClick={() => pick("accept")}>{t(lang, "yes_please")}</button>
          <button type="button" className="btn big secondary" onClick={() => pick("decline")}>{t(lang, "no_thanks")}</button>
        </div>
      </div>
    );
  }
  const c = item.content as ChoiceMenuContent;
  const card = (key: string, kind: string, stars: number) => (
    <button type="button" className="opt figure-opt" onClick={() => pick(kind)} style={{ minHeight: 170 }}>
      <strong style={{ fontSize: "1.2rem" }}>{t(lang, key)}</strong>
      <span aria-label={t(lang, "t18.stars", { n: stars })}>
        {Array.from({ length: stars }, (_, i) => <span key={i} className="star" style={{ fontSize: "2rem" }}>★</span>)}
      </span>
      <span className="muted small">{t(lang, "t18.stars", { n: stars })}</span>
    </button>
  );
  return (
    <div>
      <Prompt text={t(lang, c.prompt_key)} lang={lang} />
      <div className="options pair">
        {card("t18.familiar", "easy", c.easy_points)}
        {card("t18.new", "hard", c.hard_points)}
      </div>
    </div>
  );
}

/** T21 Habits Check: behaviour-anchored questions with no right answer. */
export function SurveyItem({ item, lang, onSubmit, onIdle }: ItemProps) {
  const c = item.content as SurveyContent;
  const timer = useItemTimer(item.id, onIdle);
  const [selected, setSelected] = useState<string | null>(null);
  const done = useRef(false);
  return (
    <div>
      <Prompt text={c.prompt} lang={lang} />
      <div className="options">
        {c.options.map((o) => (
          <OptionButton key={o.id} option={o} lang={lang} selected={selected === o.id}
            onClick={() => { timer.select(o.id); setSelected(o.id); }} />
        ))}
      </div>
      <div className="row" style={{ marginTop: "1rem" }}>
        <span className="spacer" />
        <button type="button" className="btn big" disabled={!selected}
          onClick={() => { if (!done.current) { done.current = true; onSubmit({ item, answer: selected, timer }); } }}>
          {t(lang, "next")}
        </button>
      </div>
    </div>
  );
}
