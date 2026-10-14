import { collectVoskResults, detectSpeech, framesFromLevels, type CaptureResult, type VadOptions } from "@sds/task-library";
import { SdsVoice } from "../../modules/sds-voice";
import { stopSpeaking } from "../platform";
import { installedModel } from "./models";

/**
 * Android's VOICE_RECOGNITION microphone has no automatic gain, so speech arrives quieter than in the
 * browser. A lower floor keeps quiet speakers from being missed. PILOT: tune on real phones.
 */
export const ANDROID_VAD: VadOptions = { minThreshold: 0.01 };

/**
 * Microphone capture on Android with the same shape as the web app's VoiceCapture. The native module keeps
 * audio in memory and returns energy levels and Vosk results; the features are computed here by the same
 * shared functions the web uses.
 */
export class NativeVoiceCapture {
  onLevel: ((level: number) => void) | null = null;
  private sub: { remove(): void } | null = null;
  private active = false;

  static supported(): boolean {
    return SdsVoice !== null;
  }

  /** Asks for the microphone if needed; false when the student (or Android) said no. */
  static async permit(): Promise<boolean> {
    if (!SdsVoice) return false;
    const current = await SdsVoice.getPermissionsAsync().catch(() => null);
    if (current?.granted) return true;
    if (current && !current.canAskAgain) return false;
    return (await SdsVoice.requestPermissionsAsync().catch(() => null))?.granted ?? false;
  }

  async start(language: string, useSpeechToText = true): Promise<void> {
    const voice = SdsVoice;
    if (!voice) throw new Error("voice_unavailable");
    if (!(await NativeVoiceCapture.permit())) throw new Error("mic_permission");
    await stopSpeaking(); // a spoken prompt would otherwise be heard as the student's voice
    const modelPath = useSpeechToText ? await installedModel(language) : null;
    this.sub = voice.addListener("onLevel", (e) => this.onLevel?.(e.level));
    try {
      await voice.start({ modelPath });
      this.active = true;
    } catch (e) {
      this.release();
      throw e;
    }
  }

  async stop(): Promise<CaptureResult> {
    const voice = SdsVoice;
    this.release();
    if (!voice || !this.active) return emptyResult();
    this.active = false;
    const r = await voice.stop().catch(() => null);
    if (!r) return emptyResult();
    const stt = r.results ? collectVoskResults(r.results) : null;
    return {
      vad: detectSpeech(framesFromLevels(r.levels, r.frameMs), ANDROID_VAD),
      words: stt ? stt.words : null,
      transcript: stt ? stt.text : null,
      durationMs: r.durationMs,
      inputSilent: r.inputSilent,
    };
  }

  cancel(): void {
    this.release();
    if (this.active) void SdsVoice?.cancel().catch(() => undefined);
    this.active = false;
  }

  private release(): void {
    this.sub?.remove();
    this.sub = null;
  }
}

function emptyResult(): CaptureResult {
  return { vad: detectSpeech([]), words: null, transcript: null, durationMs: 0, inputSilent: false };
}
