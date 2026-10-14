import AsyncStorage from "@react-native-async-storage/async-storage";
import Constants from "expo-constants";
import * as Speech from "expo-speech";
import { ApiClient, type StorageAdapter } from "@sds/task-library";

const extra = (Constants.expoConfig?.extra ?? {}) as { apiUrl?: string; modelsUrl?: string };
export const API_URL: string = extra.apiUrl ?? "http://10.0.2.2:8000";
/** Where the offline speech models are served (the web app's /models/ folder). */
export const MODELS_URL: string = (extra.modelsUrl ?? "http://10.0.2.2:5173/models").replace(/\/+$/, "");

export function makeClient(token: string | null): ApiClient {
  const c = new ApiClient(API_URL, (url, init) => fetch(url, init as RequestInit) as never);
  c.token = token;
  return c;
}

/** Offline buffer storage on the device. */
export const deviceStorage: StorageAdapter = {
  getItem: (k) => AsyncStorage.getItem(k),
  setItem: (k, v) => AsyncStorage.setItem(k, v),
  removeItem: (k) => AsyncStorage.removeItem(k),
};

export function speak(text: string, lang: string): void {
  Speech.stop();
  Speech.speak(text, { language: lang === "hi" ? "hi-IN" : "en-IN", rate: 0.95 });
}

/** Stops any spoken prompt so the microphone doesn't pick it up. */
export async function stopSpeaking(): Promise<void> {
  await Speech.stop().catch(() => undefined);
}

let counter = 0;
export function uuid(): string {
  const rnd = () => Math.floor(Math.random() * 0x100000000).toString(16).padStart(8, "0");
  counter = (counter + 1) % 0xffff;
  return `${rnd()}-${rnd().slice(0, 4)}-4${rnd().slice(0, 3)}-${(8 + (counter % 4)).toString(16)}${rnd().slice(0, 3)}-${rnd()}${rnd().slice(0, 4)}`;
}
