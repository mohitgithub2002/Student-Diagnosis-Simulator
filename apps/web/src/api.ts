import { ApiClient, ApiError } from "@sds/task-library";

export { ApiError };

export type Role = "student" | "parent" | "school_admin" | "teacher" | "reviewer" | "superadmin";

const KEY = "sds.auth";

export interface Auth {
  token: string;
  role: Role;
  name?: string;
  school_id?: number | null;
  student?: { id: string; name: string; language: string; age_band: string };
}

/** Tokens live in sessionStorage so a shared school-lab computer forgets them when the tab closes. */
export function getAuth(scope: "student" | "parent" | "staff"): Auth | null {
  try {
    const raw = sessionStorage.getItem(`${KEY}.${scope}`);
    return raw ? (JSON.parse(raw) as Auth) : null;
  } catch {
    return null;
  }
}

export function setAuth(scope: "student" | "parent" | "staff", auth: Auth | null): void {
  try {
    if (auth) sessionStorage.setItem(`${KEY}.${scope}`, JSON.stringify(auth));
    else sessionStorage.removeItem(`${KEY}.${scope}`);
  } catch {
    /* storage unavailable: stay signed in for this page only */
  }
}

const browserFetch = (url: string, init?: RequestInit) => fetch(url, init);

export function client(token?: string | null): ApiClient {
  const c = new ApiClient("", browserFetch as never);
  c.token = token ?? null;
  return c;
}

export async function api<T = any>(method: string, path: string, body?: unknown, token?: string | null): Promise<T> {
  return client(token).request<T>(method, path, body);
}

export async function upload<T = any>(path: string, file: File, token: string): Promise<T> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(path, { method: "POST", body: form, headers: { Authorization: `Bearer ${token}` } });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new ApiError(res.status, data.detail);
  return data as T;
}

export async function download(path: string, token: string, filename: string): Promise<void> {
  const res = await fetch(path, { headers: { Authorization: `Bearer ${token}` } });
  if (!res.ok) throw new ApiError(res.status, "Download failed");
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function errorText(e: unknown): string {
  if (e instanceof ApiError) {
    const d = e.detail as any;
    if (typeof d === "string") return d;
    if (Array.isArray(d)) return d.map((x) => x.msg ?? String(x)).join("; ");
    if (d && typeof d === "object") return d.message ?? JSON.stringify(d);
    return e.message;
  }
  return e instanceof Error ? e.message : "Something went wrong";
}
