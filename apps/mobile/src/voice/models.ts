import { voskModelFor } from "@sds/task-library";
import { SdsVoice } from "../../modules/sds-voice";
import { MODELS_URL } from "../platform";

/**
 * Offline speech models. Only the model for the student's language is downloaded, and only when the parent
 * allowed voice. Models are public data from the school's server, checked against the published SHA-256.
 */
interface ManifestEntry { zip: string; sha256: string; bytes?: number }

const installing = new Map<string, Promise<string | null>>();

/** The installed model folder for a language, or null (no model for the language, not installed, Expo Go). */
export async function installedModel(lang: string): Promise<string | null> {
  const name = voskModelFor(lang);
  if (!SdsVoice || !name) return null;
  return SdsVoice.modelPath(name).catch(() => null);
}

/** Makes sure the language's model is installed; resolves to its folder, or null if that isn't possible now. */
export function ensureModel(lang: string, onProgress?: (percent: number) => void): Promise<string | null> {
  const name = voskModelFor(lang);
  const voice = SdsVoice;
  if (!voice || !name) return Promise.resolve(null);
  const listener = voice.addListener("onModelProgress", (e) => {
    if (e.name === name && e.total > 0) onProgress?.(Math.min(100, Math.round((e.received / e.total) * 100)));
  });
  let job = installing.get(name);
  if (!job) {
    job = (async () => {
      const existing = await voice.modelPath(name).catch(() => null);
      if (existing) return existing;
      const res = await fetch(`${MODELS_URL}/manifest.json`, { headers: { Accept: "application/json" } });
      if (!res.ok) return null;
      const entry = ((await res.json()) as Record<string, ManifestEntry>)[name];
      if (!entry?.zip || !/^[0-9a-f]{64}$/i.test(entry.sha256 ?? "")) return null;
      const url = /^https?:\/\//.test(entry.zip) ? entry.zip : `${MODELS_URL}/${entry.zip}`;
      return voice.installModel(name, url, entry.sha256);
    })()
      .catch(() => null)
      .finally(() => installing.delete(name));
    installing.set(name, job);
  }
  return job.finally(() => listener.remove());
}
