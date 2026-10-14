import type { Lang } from "../types";
import type { Word } from "./features";

/**
 * Offline Vosk speech models per UI language. The web app loads `<name>.tar.gz` and the Android app
 * installs `<name>.zip`; both are served from the app's `/models/` folder (scripts/fetch-vosk-models.sh).
 */
export const VOSK_MODELS: Partial<Record<Lang, string>> = {
  en: "vosk-model-small-en-in-0.4",
  hi: "vosk-model-small-hi-0.22",
  hinglish: "vosk-model-small-hi-0.22",
};

/** The model for a language, or null when that language uses energy-only voice features. */
export function voskModelFor(lang: string): string | null {
  return VOSK_MODELS[lang as Lang] ?? null;
}

/** One Vosk result: recognised words with timings (seconds from the first sample) and the text. */
export interface VoskJson {
  result?: { word: string; start: number; end: number; conf?: number }[];
  text?: string;
}

/**
 * Collects Vosk results, given as parsed objects (vosk-browser) or JSON strings (Android), into words and
 * text. Malformed entries are skipped so a bad segment never loses the rest of the answer.
 */
export function collectVoskResults(items: Iterable<VoskJson | string>): { words: Word[]; text: string } {
  const words: Word[] = [];
  const texts: string[] = [];
  for (const raw of items) {
    let parsed: VoskJson | null = null;
    try {
      parsed = typeof raw === "string" ? (JSON.parse(raw) as VoskJson) : raw;
    } catch {
      continue;
    }
    if (!parsed || typeof parsed !== "object") continue;
    for (const w of Array.isArray(parsed.result) ? parsed.result : []) {
      if (typeof w?.word === "string" && Number.isFinite(w.start) && Number.isFinite(w.end)) {
        words.push({ word: w.word, start: w.start, end: w.end });
      }
    }
    if (typeof parsed.text === "string" && parsed.text.trim()) texts.push(parsed.text.trim());
  }
  return { words, text: texts.join(" ") };
}
