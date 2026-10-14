import { collectVoskResults, voskModelFor, type VoskJson, type Word } from "@sds/task-library";

/**
 * Optional on-device speech-to-text with Vosk (WebAssembly). Models are not bundled: run
 * scripts/fetch-vosk-models.sh to place them under public/models/. Without a model the app still
 * measures speech timing with the energy detector; only word-level features are skipped.
 */
function modelUrl(language: string): string | null {
  const name = voskModelFor(language);
  return name ? `/models/${name}.tar.gz` : null;
}

export interface Recognizer {
  accept(buffer: AudioBuffer): void;
  finish(): Promise<{ words: Word[]; text: string }>;
  dispose(): void;
}

const modelCache = new Map<string, Promise<any | null>>();

async function modelAvailable(url: string): Promise<boolean> {
  try {
    const res = await fetch(url, { method: "HEAD" });
    return res.ok && !(res.headers.get("content-type") ?? "").includes("text/html");
  } catch {
    return false;
  }
}

async function loadModel(language: string): Promise<any | null> {
  const url = modelUrl(language);
  if (!url) return null;
  if (!modelCache.has(url)) {
    modelCache.set(url, (async () => {
      if (!(await modelAvailable(url))) return null;
      const vosk = await import("vosk-browser").catch(() => null);
      if (!vosk) return null;
      return vosk.createModel(url);
    })());
  }
  return modelCache.get(url)!;
}

export async function speechToTextAvailable(language: string): Promise<boolean> {
  return (await loadModel(language)) !== null;
}

export async function loadRecognizer(language: string, sampleRate: number): Promise<Recognizer | null> {
  const model = await loadModel(language);
  if (!model) return null;
  const rec = new model.KaldiRecognizer(sampleRate);
  rec.setWords(true);
  const results: VoskJson[] = [];
  let resolveFinal: (() => void) | null = null;
  rec.on("result", (msg: any) => {
    if (msg.result) results.push(msg.result);
    resolveFinal?.();
  });
  return {
    accept: (buffer) => {
      try {
        rec.acceptWaveform(buffer);
      } catch {
        /* recogniser busy or removed */
      }
    },
    finish: () =>
      new Promise((resolve) => {
        let finished = false;
        const done = () => {
          if (finished) return;
          finished = true;
          rec.remove();
          resolve(collectVoskResults(results));
        };
        resolveFinal = done;
        rec.retrieveFinalResult();
        window.setTimeout(done, 1500); // never hang the session on the recogniser
      }),
    dispose: () => rec.remove(),
  };
}
