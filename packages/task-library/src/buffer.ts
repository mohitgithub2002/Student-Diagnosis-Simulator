import type { FeatureRow, ItemEvent } from "./types";

/**
 * Offline buffer (PRD: sessions survive a dropped connection). Every event, feature and session
 * completion is written to device storage first, then synced in order; failed syncs are retried later.
 * Event ids make the server ingest idempotent, so re-sending after a timeout is safe.
 */

export interface StorageAdapter {
  getItem(key: string): Promise<string | null>;
  setItem(key: string, value: string): Promise<void>;
  removeItem(key: string): Promise<void>;
}

export type Op =
  | { type: "events"; session: number; events: ItemEvent[] }
  | { type: "features"; session: number; features: FeatureRow[] }
  | { type: "state"; session: number; state: Record<string, unknown> }
  | { type: "complete"; session: number };

export interface Transport {
  send(op: Op): Promise<void>;
}

export class MemoryStorage implements StorageAdapter {
  private data = new Map<string, string>();
  async getItem(key: string) {
    return this.data.get(key) ?? null;
  }
  async setItem(key: string, value: string) {
    this.data.set(key, value);
  }
  async removeItem(key: string) {
    this.data.delete(key);
  }
}

export class OfflineBuffer {
  private queue: Op[] | null = null;
  private flushing: Promise<boolean> | null = null;
  private listeners = new Set<(pending: number) => void>();

  constructor(private storage: StorageAdapter, private key = "sds.queue") {}

  private async load(): Promise<Op[]> {
    if (this.queue) return this.queue;
    const raw = await this.storage.getItem(this.key);
    this.queue = raw ? (JSON.parse(raw) as Op[]) : [];
    return this.queue;
  }

  private async save(): Promise<void> {
    await this.storage.setItem(this.key, JSON.stringify(this.queue ?? []));
    this.listeners.forEach((fn) => fn(this.queue?.length ?? 0));
  }

  onChange(fn: (pending: number) => void): () => void {
    this.listeners.add(fn);
    return () => this.listeners.delete(fn);
  }

  async pending(): Promise<number> {
    return (await this.load()).length;
  }

  async push(op: Op): Promise<void> {
    const q = await this.load();
    const last = q[q.length - 1];
    if (op.type === "events" && last?.type === "events" && last.session === op.session && last.events.length < 100) {
      last.events.push(...op.events); // batch small writes
    } else if (op.type === "state" && last?.type === "state" && last.session === op.session) {
      last.state = op.state;
    } else {
      q.push(op);
    }
    await this.save();
  }

  /** Send queued operations in order. Returns true when the queue is empty. */
  flush(transport: Transport): Promise<boolean> {
    if (!this.flushing) {
      this.flushing = (async () => {
        const q = await this.load();
        try {
          while (q.length) {
            await transport.send(q[0]);
            q.shift();
            await this.save();
          }
          return true;
        } catch {
          return false;
        } finally {
          this.flushing = null;
        }
      })();
    }
    return this.flushing;
  }
}
