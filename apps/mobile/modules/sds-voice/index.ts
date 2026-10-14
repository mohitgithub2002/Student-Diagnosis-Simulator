import { NativeModule, requireOptionalNativeModule, type PermissionResponse } from "expo";

/** What the native capture hands back: numbers and Vosk results only, never audio. */
export interface NativeStopResult {
  levels: number[]; // RMS per frame, 0..1
  frameMs: number;
  durationMs: number;
  results: string[] | null; // Vosk JSON per utterance; null when speech-to-text was off or dropped
  sttDropped: string | null; // why speech-to-text was dropped: "model", "backlog", "timeout"
  inputSilent: boolean;
}

type Events = {
  onLevel: (e: { level: number }) => void;
  onModelProgress: (e: { name: string; received: number; total: number }) => void;
};

declare class SdsVoiceModule extends NativeModule<Events> {
  getPermissionsAsync(): Promise<PermissionResponse>;
  requestPermissionsAsync(): Promise<PermissionResponse>;
  start(options: { modelPath?: string | null }): Promise<{ stt: boolean }>;
  stop(): Promise<NativeStopResult>;
  cancel(): Promise<void>;
  modelPath(name: string): Promise<string | null>;
  preloadModel(path: string): Promise<boolean>;
  installModel(name: string, url: string, sha256: string): Promise<string>;
  releaseModels(): Promise<void>;
}

/** The native voice module, or null in Expo Go, where the app falls back to typed answers and silent reading. */
export const SdsVoice = requireOptionalNativeModule<SdsVoiceModule>("SdsVoice");
