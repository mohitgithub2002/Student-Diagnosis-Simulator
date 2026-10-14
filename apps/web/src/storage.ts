import { MemoryStorage, type StorageAdapter } from "@sds/task-library";

/** IndexedDB key-value store for the offline buffer, with an in-memory fallback (private mode etc.). */
export class IdbStorage implements StorageAdapter {
  private db: Promise<IDBDatabase>;

  constructor(name = "sds-offline") {
    this.db = new Promise((resolve, reject) => {
      const req = indexedDB.open(name, 1);
      req.onupgradeneeded = () => req.result.createObjectStore("kv");
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error);
    });
  }

  private async tx<T>(mode: IDBTransactionMode, fn: (s: IDBObjectStore) => IDBRequest<T>): Promise<T> {
    const db = await this.db;
    return new Promise((resolve, reject) => {
      const req = fn(db.transaction("kv", mode).objectStore("kv"));
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error);
    });
  }

  async getItem(key: string): Promise<string | null> {
    return ((await this.tx("readonly", (s) => s.get(key))) as string | undefined) ?? null;
  }

  async setItem(key: string, value: string): Promise<void> {
    await this.tx("readwrite", (s) => s.put(value, key));
  }

  async removeItem(key: string): Promise<void> {
    await this.tx("readwrite", (s) => s.delete(key));
  }
}

export function deviceStorage(): StorageAdapter {
  try {
    if (typeof indexedDB !== "undefined") return new IdbStorage();
  } catch {
    /* fall through */
  }
  return new MemoryStorage();
}
