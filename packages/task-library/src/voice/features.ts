import { textFeatures, tokenize } from "../text";
import type { FeatureChannel } from "../types";
import type { VadResult } from "./vad";

/** A recognised word with timings, as produced by on-device speech-to-text (Vosk). */
export interface Word {
  word: string;
  start: number; // seconds
  end: number; // seconds
}

/** Word-level edit distance between the passage and what was read: substitutions, deletions, insertions. */
export function alignErrors(reference: string[], spoken: string[]): number {
  const n = reference.length;
  const m = spoken.length;
  let prev = Array.from({ length: m + 1 }, (_, j) => j);
  for (let i = 1; i <= n; i++) {
    const cur = [i];
    for (let j = 1; j <= m; j++) {
      const cost = reference[i - 1] === spoken[j - 1] ? 0 : 1;
      cur[j] = Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost);
    }
    prev = cur;
  }
  return prev[m];
}

/** Repeated words or restarted phrases ("the the", "went to went to the") count as self-corrections. */
export function selfCorrections(words: string[]): number {
  let count = 0;
  for (let i = 1; i < words.length; i++) {
    if (words[i] === words[i - 1]) count++;
    else if (i >= 3 && words[i] === words[i - 2] && words[i - 1] !== words[i - 3]) {
      // "to went to" style restart
      if (words[i + 1] !== undefined && words[i + 1] === words[i - 1]) count++;
    }
  }
  return count;
}

export interface NamedFeature {
  name: string;
  value: number;
  channel: FeatureChannel;
}

const r = (x: number, d = 3) => Math.round(x * 10 ** d) / 10 ** d;

/** T7 Read Aloud features from Vosk words (channel "voice"). */
export function readAloudFromWords(passage: string, words: Word[], recordingStartS = 0): NamedFeature[] {
  if (!words.length) return [];
  const ref = tokenize(passage);
  const spoken = words.map((w) => w.word.toLowerCase());
  const durationMin = Math.max((words[words.length - 1].end - words[0].start) / 60, 1 / 60);
  let pauses = 0;
  for (let i = 1; i < words.length; i++) if (words[i].start - words[i - 1].end >= 0.5) pauses++;
  const errors = alignErrors(ref, spoken);
  return [
    { name: "t7.wpm", value: r(spoken.length / durationMin, 1), channel: "voice" },
    { name: "t7.error_rate", value: r(Math.min(1, errors / Math.max(1, ref.length))), channel: "voice" },
    { name: "t7.pause_rate", value: r((pauses / Math.max(1, spoken.length)) * 100, 2), channel: "voice" },
    { name: "t7.self_corrections", value: r((selfCorrections(spoken) / Math.max(1, spoken.length)) * 100, 2), channel: "voice" },
    { name: "t7.speech_start_ms", value: Math.round((words[0].start - recordingStartS) * 1000), channel: "voice" },
  ];
}

/** T7 features from energy-based detection only (channel "voice_vad"): reading speed is an estimate that
 * assumes the whole passage was read; there is no error rate without speech-to-text. */
export function readAloudFromVad(wordCount: number, vad: VadResult): NamedFeature[] {
  if (!vad.span_ms || vad.speech_start_ms === null) return [];
  return [
    { name: "t7.wpm", value: r(wordCount / (vad.span_ms / 60000), 1), channel: "voice_vad" },
    { name: "t7.pause_rate", value: r((vad.pause_count / Math.max(1, wordCount)) * 100, 2), channel: "voice_vad" },
    { name: "t7.speech_start_ms", value: vad.speech_start_ms, channel: "voice_vad" },
  ];
}

/** T11/T22 features from a typed answer or a transcript (text is discarded after this call). */
export function answerFromText(prefix: "t11" | "t22", text: string, channel: FeatureChannel, keywords?: string[],
  extra?: { speech_start_ms?: number; pauses?: number }): NamedFeature[] {
  const f = textFeatures(text, keywords);
  const out: NamedFeature[] = Object.entries(f).map(([k, v]) => ({ name: `${prefix}.${k}`, value: v as number, channel }));
  if (extra?.speech_start_ms !== undefined) out.push({ name: `${prefix}.speech_start_ms`, value: extra.speech_start_ms, channel });
  if (extra?.pauses !== undefined && f.word_count) {
    out.push({ name: `${prefix}.pause_rate`, value: r((extra.pauses / f.word_count) * 100, 2), channel });
  }
  return out;
}

/** T11/T22 spoken answer without speech-to-text: timing only, no word-based rubric. */
export function answerFromVad(prefix: "t11" | "t22", vad: VadResult): NamedFeature[] {
  if (vad.speech_start_ms === null) return [];
  return [
    { name: `${prefix}.speech_start_ms`, value: vad.speech_start_ms, channel: "voice_vad" },
    { name: `${prefix}.speaking_s`, value: r(vad.speaking_ms / 1000, 1), channel: "voice_vad" },
    // About 2 words per second of speech; marked voice_vad so the server never builds a rubric from it.
    { name: `${prefix}.word_count`, value: Math.round((vad.speaking_ms / 1000) * 2), channel: "voice_vad" },
  ];
}
