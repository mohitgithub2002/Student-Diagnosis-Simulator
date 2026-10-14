import type { BundleItem, FeatureRow, Lang, Presentation } from "@sds/task-library";
import { AllocateItem } from "./items/AllocateItem";
import { ChoiceItem } from "./items/ChoiceItem";
import type { SubmitFn } from "./items/common";
import { EstimateItem } from "./items/EstimateItem";
import { PassageItem } from "./items/PassageItem";
import { PlanRouteItem } from "./items/PlanRouteItem";
import { SequenceItem } from "./items/SequenceItem";
import { MenuItem, SurveyItem } from "./items/SmallItems";
import { StreamItem } from "./items/StreamItem";
import { TextResponseItem } from "./items/TextResponseItem";

/** Maps an item's interaction primitive to its renderer. */
export function ItemRenderer({ p, lang, aux, voiceAllowed, onSubmit, onIdle, onFeatures }: {
  p: Presentation;
  lang: Lang;
  aux: Record<string, BundleItem>;
  voiceAllowed: boolean;
  onSubmit: SubmitFn;
  onIdle: (ms: number) => void;
  onFeatures: (rows: FeatureRow[]) => void;
}) {
  const props = {
    item: p.item, taskId: p.entry.task_id, lang, settings: p.settings, condition: p.condition, onSubmit, onIdle, aux,
    voiceAllowed, onFeatures, previous: p.previous ? { answer: p.previous.answer } : undefined, index: p.index,
  };
  switch (p.item.content.kind) {
    case "sequence":
      return <SequenceItem {...props} />;
    case "choice":
      return <ChoiceItem {...props} />;
    case "estimate":
      return <EstimateItem {...props} />;
    case "stream":
      return <StreamItem {...props} />;
    case "passage_questions":
      return <PassageItem {...props} />;
    case "text_response":
      return <TextResponseItem {...props} />;
    case "plan_route":
      return <PlanRouteItem {...props} />;
    case "allocate":
      return <AllocateItem {...props} />;
    case "choice_menu":
    case "bonus_offer":
      return <MenuItem {...props} />;
    case "survey":
      return <SurveyItem {...props} />;
    default:
      return <p>Unsupported item</p>;
  }
}
