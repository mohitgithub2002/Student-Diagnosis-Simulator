import type { Word } from "./features";
import type { Frame, VadResult } from "./vad";

/**
 * What a voice capture hands back once the microphone is closed. The audio itself is never kept: only
 * energy-based timing, and recognised words when a speech model is installed.
 */
export interface CaptureResult {
  vad: VadResult;
  words: Word[] | null; // null when no speech-to-text model is available
  transcript: string | null; // kept in memory only so features can be computed, then discarded
  durationMs: number;
  inputSilent?: boolean; // the microphone delivered pure silence (e.g. Android's mic privacy switch)
}

/** Turns evenly spaced energy levels (one per frame) into timestamped frames for `detectSpeech`. */
export function framesFromLevels(levels: ArrayLike<number>, frameMs = 20): Frame[] {
  return Array.from(levels, (rms, i) => ({ t: i * frameMs, rms }));
}
