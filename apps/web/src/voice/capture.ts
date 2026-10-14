import { detectSpeech, rms, type CaptureResult, type Frame, type Word } from "@sds/task-library";
import { loadRecognizer, type Recognizer } from "./vosk";

export type { CaptureResult };

/**
 * On-device voice capture (FR-11). Audio is read frame by frame from the microphone into memory, turned
 * into numbers (energy levels and, when a Vosk model is installed, recognised words with timings) and then
 * dropped. Nothing is recorded, stored or uploaded; there is no MediaRecorder anywhere in the app.
 */
export class VoiceCapture {
  private ctx: AudioContext | null = null;
  private stream: MediaStream | null = null;
  private frames: Frame[] = [];
  private started = 0;
  private timer: number | null = null;
  private recognizer: Recognizer | null = null;
  private processor: ScriptProcessorNode | null = null;
  onLevel: ((level: number) => void) | null = null;

  static supported(): boolean {
    return typeof navigator !== "undefined" && !!navigator.mediaDevices?.getUserMedia && typeof AudioContext !== "undefined";
  }

  async start(language: string, useSpeechToText = true): Promise<void> {
    this.stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true } });
    this.ctx = new AudioContext();
    const source = this.ctx.createMediaStreamSource(this.stream);
    const analyser = this.ctx.createAnalyser();
    analyser.fftSize = 1024;
    source.connect(analyser);
    const buf = new Float32Array(analyser.fftSize);
    this.frames = [];
    this.started = performance.now();
    this.timer = window.setInterval(() => {
      analyser.getFloatTimeDomainData(buf);
      const level = rms(buf);
      this.frames.push({ t: performance.now() - this.started, rms: level });
      this.onLevel?.(level);
    }, 20);
    if (useSpeechToText) {
      this.recognizer = await loadRecognizer(language, this.ctx.sampleRate).catch(() => null);
      if (this.recognizer) {
        // ScriptProcessor is deprecated but universally available; samples go straight to the recogniser.
        this.processor = this.ctx.createScriptProcessor(4096, 1, 1);
        this.processor.onaudioprocess = (e) => this.recognizer?.accept(e.inputBuffer);
        source.connect(this.processor);
        this.processor.connect(this.ctx.destination);
      }
    }
  }

  get hasSpeechToText(): boolean {
    return this.recognizer !== null;
  }

  async stop(): Promise<CaptureResult> {
    if (this.timer !== null) window.clearInterval(this.timer);
    const durationMs = performance.now() - this.started;
    let words: Word[] | null = null;
    let transcript: string | null = null;
    if (this.recognizer) {
      const out = await this.recognizer.finish();
      words = out.words;
      transcript = out.text;
    }
    this.processor?.disconnect();
    this.stream?.getTracks().forEach((t) => t.stop());
    await this.ctx?.close().catch(() => undefined);
    const vad = detectSpeech(this.frames);
    this.frames = [];
    return { vad, words, transcript, durationMs };
  }

  cancel(): void {
    if (this.timer !== null) window.clearInterval(this.timer);
    this.recognizer?.dispose();
    this.processor?.disconnect();
    this.stream?.getTracks().forEach((t) => t.stop());
    this.ctx?.close().catch(() => undefined);
    this.frames = [];
  }
}
