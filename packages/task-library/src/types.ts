/** Shapes shared with the API (backend/app/services/bundle.py and backend/app/api/schemas.py). */

export type Lang = "en" | "hi" | "hinglish";
export type ReportLang = "en" | "hi";
export type AgeBand = "11-14" | "15-18";

export type Fill = "solid" | "empty" | "striped" | "dotted";

export interface Figure {
  shape: string;
  rotation: number;
  count: number;
  fill: Fill;
  cells?: number[][];
}

export interface Option {
  id: string;
  text?: string;
  label_key?: string;
  figure?: Figure;
  value?: number;
}

export interface Question {
  id: string;
  qtype: string;
  prompt: string;
  options: Option[];
  set?: string;
}

export type ItemContent =
  | SequenceContent
  | ChoiceContent
  | EstimateContent
  | StreamContent
  | PassageQuestionsContent
  | TextResponseContent
  | PlanRouteContent
  | AllocateContent
  | ChoiceMenuContent
  | BonusOfferContent
  | SurveyContent;

export interface SequenceContent {
  kind: "sequence";
  mode: "digits" | "symbols" | "colors";
  direction: "forward" | "backward";
  sequence: string[];
  choices: string[];
  show_ms: number;
  gap_ms: number;
  prompt_key: string;
}

export interface ChoiceContent {
  kind: "choice";
  layout: "list" | "grid" | "pair" | "steps";
  prompt?: string;
  prompt_key?: string;
  stem?: Record<string, unknown>;
  options: Option[];
  concept?: string;
  steps?: number;
  show_ms?: number;
  condition?: "relaxed" | "pressure";
  pair?: number;
}

export interface EstimateContent {
  kind: "estimate";
  prompt_key: string;
  min: number;
  max: number;
  step: number;
  target: number;
  concept?: string;
}

export interface StreamContent {
  kind: "stream";
  prompt_key: string;
  target: Figure;
  distractors: Figure[];
  duration_ms: number;
  isi_ms: number;
  stim_ms: number;
  target_rate: number;
  seed: number;
}

export interface PassageQuestionsContent {
  kind: "passage_questions";
  mode: "card" | "passage" | "lesson";
  card?: { title: string; lines: string[] };
  passage?: { title: string; text: string; word_count: number };
  lesson?: { title: string; sections: string[] };
  recap?: { text: string; study_s: number };
  study_s?: number;
  questions: Question[];
}

export interface TextResponseContent {
  kind: "text_response";
  mode: "read_aloud" | "explain" | "converse";
  title?: string;
  passage?: string;
  word_count?: number;
  prompt?: string;
  keywords?: string[];
  time_limit_s: number;
}

export interface PlanRouteContent {
  kind: "plan_route";
  prompt_key: string;
  grid: number;
  start: [number, number];
  places: { id: string; label_key: string; pos: [number, number] }[];
}

export interface AllocateContent {
  kind: "allocate";
  prompt_key: string;
  total_s: number;
  blocks: { id: string; label_key: string; difficulty: "easy" | "medium" | "hard"; item_ids: string[] }[];
}

export interface ChoiceMenuContent {
  kind: "choice_menu";
  prompt_key: string;
  easy_ref: string;
  hard_ref: string;
  easy_points: number;
  hard_points: number;
}

export interface BonusOfferContent {
  kind: "bonus_offer";
  prompt_key: string;
  refs: string[];
}

export interface SurveyContent {
  kind: "survey";
  qid: string;
  prompt: string;
  options: Option[];
}

export interface BundleItem {
  id: string;
  task_id: string;
  level: number;
  language: string;
  content: ItemContent;
  answer_key: Record<string, any>;
  tags: string[];
  variant_group: string;
}

export interface TaskEntry {
  task_id: string;
  variant: string;
  name: string;
  title: string;
  instructions: string;
  instructions_all: Record<Lang, string>;
  primitive: string;
  minutes: number;
  adaptive: boolean;
  confidence: boolean;
  language: string;
  settings: Record<string, any>;
  items: BundleItem[];
  pools?: Record<string, BundleItem[]> | Record<string, Record<string, BundleItem[]>>;
  start_level?: number;
  items_per_run?: number | Record<string, number>;
}

export interface Bundle {
  session_number: number;
  focus: string;
  age_band: AgeBand;
  language: Lang;
  seed: number;
  confidence_scale: number;
  tasks: TaskEntry[];
  aux_items: Record<string, BundleItem>;
}

export interface ChangeEntry {
  from: unknown;
  to: unknown;
  at_ms: number;
}

/** One logged response, as sent to POST /api/student/sessions/{n}/events (FR-10). */
export interface ItemEvent {
  client_event_id: string;
  item_id: string;
  task_id: string;
  seq: number;
  shown_at_ms: number;
  response_ms: number | null;
  first_click_ms: number | null;
  answer: unknown;
  client_correct: boolean | null;
  changes: number;
  change_log: ChangeEntry[];
  skipped: boolean;
  retries: number;
  confidence: number | null;
  idle_ms: number;
  max_idle_ms: number;
  switches: number;
  language: string;
  condition: string;
  extra: Record<string, unknown>;
}

export type FeatureChannel = "voice" | "voice_vad" | "text" | "device";

export interface FeatureRow {
  name: string;
  value: number;
  channel: FeatureChannel;
  task_id: string;
  item_id: string;
}
