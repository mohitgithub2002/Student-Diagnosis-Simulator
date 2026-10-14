/**
 * Energy-based voice activity detection over short frames (about 20 ms). Pure math: the web app feeds
 * RMS levels from a Web Audio AnalyserNode; audio samples are never stored or uploaded.
 */

export interface Frame {
  t: number; // ms since recording started
  rms: number; // 0..1
}

export interface VadResult {
  speech_start_ms: number | null;
  speaking_ms: number;
  span_ms: number; // first speech to last speech
  pause_count: number; // silences of >= minPauseMs inside the speech span
  pause_total_ms: number;
  segments: { start: number; end: number }[];
}

export interface VadOptions {
  noisePercentile?: number;
  minSpeechMs?: number;
  minPauseMs?: number;
  thresholdFactor?: number;
  minThreshold?: number;
}

export function detectSpeech(frames: Frame[], opts: VadOptions = {}): VadResult {
  const minSpeechMs = opts.minSpeechMs ?? 120;
  const minPauseMs = opts.minPauseMs ?? 400;
  const factor = opts.thresholdFactor ?? 3;
  // Noise floor: a low percentile of all frames, so speaking straight away does not raise the threshold.
  const sorted = frames.map((f) => f.rms).sort((a, b) => a - b);
  const noise = sorted.length ? sorted[Math.floor(sorted.length * (opts.noisePercentile ?? 0.2))] : 0.01;
  const threshold = Math.max(opts.minThreshold ?? 0.02, noise * factor);

  const raw: { start: number; end: number }[] = [];
  let open: number | null = null;
  let last = 0;
  for (const f of frames) {
    const speaking = f.rms >= threshold;
    if (speaking && open === null) open = f.t;
    if (!speaking && open !== null) {
      raw.push({ start: open, end: f.t });
      open = null;
    }
    last = f.t;
  }
  if (open !== null) raw.push({ start: open, end: last });

  // Merge segments separated by gaps shorter than a pause, then drop blips.
  const merged: { start: number; end: number }[] = [];
  for (const seg of raw) {
    const prev = merged[merged.length - 1];
    if (prev && seg.start - prev.end < minPauseMs) prev.end = seg.end;
    else merged.push({ ...seg });
  }
  const segments = merged.filter((s) => s.end - s.start >= minSpeechMs);
  if (!segments.length) {
    return { speech_start_ms: null, speaking_ms: 0, span_ms: 0, pause_count: 0, pause_total_ms: 0, segments: [] };
  }
  let pauseTotal = 0;
  for (let i = 1; i < segments.length; i++) pauseTotal += segments[i].start - segments[i - 1].end;
  return {
    speech_start_ms: Math.round(segments[0].start),
    speaking_ms: Math.round(segments.reduce((a, s) => a + (s.end - s.start), 0)),
    span_ms: Math.round(segments[segments.length - 1].end - segments[0].start),
    pause_count: segments.length - 1,
    pause_total_ms: Math.round(pauseTotal),
    segments,
  };
}

export function rms(samples: ArrayLike<number>): number {
  let sum = 0;
  for (let i = 0; i < samples.length; i++) sum += samples[i] * samples[i];
  return samples.length ? Math.sqrt(sum / samples.length) : 0;
}
