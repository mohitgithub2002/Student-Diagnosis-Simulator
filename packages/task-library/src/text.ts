/**
 * On-device text features for typed or transcribed answers (T11, T22). Only these numbers leave the
 * device; the text itself is discarded (PRD: no free-form transcripts are stored).
 */

const CONNECTORS = new Set([
  // English
  "first", "then", "next", "after", "finally", "because", "so", "but", "also", "however", "since", "if", "when",
  "therefore", "before", "later", "instead",
  // Hindi (Devanagari)
  "पहले", "फिर", "बाद", "क्योंकि", "इसलिए", "लेकिन", "पर", "अगर", "तो", "जब", "आखिर", "भी",
  // Hinglish
  "pehle", "phir", "baad", "kyunki", "isliye", "lekin", "par", "agar", "toh", "jab", "aakhir", "bhi",
]);

const FILLERS = new Set(["um", "uh", "umm", "hmm", "like", "matlab", "woh", "haan", "accha", "मतलब", "वो", "हाँ", "अच्छा"]);

export function tokenize(text: string): string[] {
  return text
    .toLowerCase()
    .replace(/[^\p{L}\p{M}\p{N}\s'-]/gu, " ")
    .split(/\s+/)
    .filter(Boolean);
}

export interface TextFeatures {
  word_count: number;
  unique_ratio: number;
  connectors: number;
  avg_sentence_words: number;
  filler_rate: number;
  keyword_share?: number;
}

export function textFeatures(text: string, keywords?: string[]): TextFeatures {
  const words = tokenize(text);
  const sentences = text.split(/[.!?।\n]+/).map((s) => s.trim()).filter(Boolean);
  const unique = new Set(words);
  const out: TextFeatures = {
    word_count: words.length,
    unique_ratio: words.length ? round(unique.size / words.length) : 0,
    connectors: words.filter((w) => CONNECTORS.has(w)).length,
    avg_sentence_words: sentences.length ? round(words.length / sentences.length) : words.length,
    filler_rate: words.length ? round(words.filter((w) => FILLERS.has(w)).length / words.length) : 0,
  };
  if (keywords && keywords.length) {
    const lowered = words.join(" ");
    const hits = keywords.filter((k) => lowered.includes(k.toLowerCase())).length;
    out.keyword_share = round(hits / keywords.length);
  }
  return out;
}

function round(x: number): number {
  return Math.round(x * 1000) / 1000;
}
