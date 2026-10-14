import type { TextResponseContent } from "../types";
import type { CaptureResult } from "./capture";
import {
  answerFromText, answerFromVad, readAloudFromVad, readAloudFromWords, type NamedFeature,
} from "./features";

/**
 * How Read Aloud (T7), Explain It (T11) and Guided Conversation (T22) turn an answer into features. Shared
 * by the web and Android apps so both send the same numbers for the same answer.
 */
export type TextMode = "choose" | "voice" | "typed" | "silent";

type Mode = Pick<TextResponseContent, "mode">;

export function textPrefix(c: Mode): "t11" | "t22" {
  return c.mode === "explain" ? "t11" : "t22";
}

/** Without voice: read silently, or type the answer. */
export function fallbackTextMode(c: Mode): TextMode {
  return c.mode === "read_aloud" ? "silent" : "typed";
}

/** Read Aloud goes straight to the microphone; open answers let the student choose speaking or typing. */
export function initialTextMode(c: Mode, canVoice: boolean): TextMode {
  if (!canVoice) return fallbackTextMode(c);
  return c.mode === "read_aloud" ? "voice" : "choose";
}

export interface ItemOutcome {
  features: NamedFeature[];
  extra: Record<string, unknown>;
  skipped: boolean;
}

/** Features from a finished voice capture: words when speech-to-text ran, otherwise energy timing only. */
export function voiceOutcome(c: TextResponseContent, res: Pick<CaptureResult, "vad" | "words" | "transcript">): ItemOutcome {
  const readAloud = c.mode === "read_aloud";
  let features: NamedFeature[];
  if (readAloud) {
    features = res.words?.length ? readAloudFromWords(c.passage ?? "", res.words) : readAloudFromVad(c.word_count ?? 0, res.vad);
  } else if (res.transcript) {
    features = answerFromText(textPrefix(c), res.transcript, "voice", c.keywords, {
      speech_start_ms: res.vad.speech_start_ms ?? undefined,
      pauses: res.vad.pause_count,
    });
  } else {
    features = answerFromVad(textPrefix(c), res.vad);
  }
  return {
    features,
    extra: { mode: "voice", stt: Boolean(res.words?.length) },
    skipped: !readAloud && res.vad.speech_start_ms === null,
  };
}

/** Features from a typed answer. The text itself is discarded by the caller. */
export function typedOutcome(c: TextResponseContent, text: string): ItemOutcome {
  return {
    features: answerFromText(textPrefix(c), text, "text", c.keywords),
    extra: { mode: "typed" },
    skipped: text.trim().length === 0,
  };
}
