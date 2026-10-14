import type { Word } from "@sds/task-library";

/**
 * Optional on-device speech-to-text with Vosk (WebAssembly). Models are not bundled: run
 * scripts/fetch-vosk-models.sh to place them under public/models/. Without a model the app still
 * measures speech timing with the energy detector; only word-level features are skipped.
 */
const MODELS: Record<string, string> = {
  en: "/models/vosk-model-small-en-in-0.4.tar.gz",
  hi: "/models/vosk-model-small-hi-0.22.tar.gz",
  hinglish: "/models/vosk-model-small-hi-0.22.tar.gz",
};

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
  const url = MODELS[language] ?? MODELS.en;
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
  const words: Word[] = [];
  const texts: string[] = [];
  let resolveFinal: (() => void) | null = null;
  rec.on("result", (msg: any) => {
    const result = msg.result;
    if (result?.result) words.push(...result.result.map((w: any) => ({ word: w.word, start: w.start, end: w.end })));
    if (result?.text) texts.push(result.text);
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
        const done = () => {
          rec.remove();
          resolve({ words, text: texts.join(" ") });
        };
        resolveFinal = done;
        rec.retrieveFinalResult();
        window.setTimeout(done, 1500); // never hang the session on the recogniser
      }),
    dispose: () => rec.remove(),
  };
}
