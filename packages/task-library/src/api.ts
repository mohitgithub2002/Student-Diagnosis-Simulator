import type { Op, Transport } from "./buffer";
import type { Bundle, Lang } from "./types";

/** Minimal fetch signature so the library has no DOM or React Native type dependency. */
export type FetchLike = (url: string, init?: {
  method?: string;
  headers?: Record<string, string>;
  body?: string;
}) => Promise<{ ok: boolean; status: number; json(): Promise<any>; text(): Promise<string> }>;

export class ApiError extends Error {
  constructor(readonly status: number, readonly detail: unknown) {
    super(typeof detail === "string" ? detail : `Request failed (${status})`);
  }
}

export class ApiClient implements Transport {
  token: string | null = null;

  constructor(private base: string, private fetcher: FetchLike) {}

  async request<T = any>(method: string, path: string, body?: unknown): Promise<T> {
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (this.token) headers.Authorization = `Bearer ${this.token}`;
    const res = await this.fetcher(`${this.base}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    if (!res.ok) {
      let detail: unknown = null;
      try {
        detail = (await res.json()).detail;
      } catch {
        detail = await res.text().catch(() => null);
      }
      throw new ApiError(res.status, detail);
    }
    return res.status === 204 ? (undefined as T) : res.json();
  }

  studentLogin(classCode: string, pin: string) {
    return this.request<{ token: string; student: { id: string; name: string; language: Lang; age_band: string } }>(
      "POST", "/api/auth/student/login", { class_code: classCode, pin });
  }

  home() {
    return this.request("GET", "/api/student/home");
  }

  warmup(language: Lang, micOk: boolean, audioOk: boolean) {
    return this.request("POST", "/api/student/warmup", { language, mic_ok: micOk, audio_ok: audioOk });
  }

  startSession(n: number, deviceType: string) {
    return this.request<{ session_id: number; number: number; voice_allowed: boolean; resume_state: Record<string, any>; bundle: Bundle }>(
      "POST", `/api/student/sessions/${n}/start`, { device_type: deviceType });
  }

  studentReport() {
    return this.request("GET", "/api/student/report");
  }

  /** Transport for the offline buffer. */
  async send(op: Op): Promise<void> {
    switch (op.type) {
      case "events":
        await this.request("POST", `/api/student/sessions/${op.session}/events`, { events: op.events });
        return;
      case "features":
        await this.request("POST", `/api/student/sessions/${op.session}/features`, { features: op.features });
        return;
      case "state":
        await this.request("PUT", `/api/student/sessions/${op.session}/state`, { state: op.state });
        return;
      case "complete":
        try {
          await this.request("POST", `/api/student/sessions/${op.session}/complete`);
        } catch (e) {
          if (e instanceof ApiError && e.status === 409) return; // already completed on an earlier attempt
          throw e;
        }
    }
  }
}
