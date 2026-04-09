const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function getApiUrl(path = ""): string {
  return `${API_URL}${path}`;
}

export function clearSession() {
  if (typeof window === "undefined") return;
  sessionStorage.removeItem("user");
}

export function getUser() {
  if (typeof window === "undefined") return null;
  const stored = sessionStorage.getItem("user");
  return stored ? JSON.parse(stored) : null;
}

export function setUser(user: object) {
  if (typeof window === "undefined") return;
  sessionStorage.setItem("user", JSON.stringify(user));
}

let isRefreshing = false;
let refreshQueue: Array<(ok: boolean) => void> = [];

function shouldAttemptRefresh(path: string): boolean {
  return !path.startsWith("/auth/login")
    && !path.startsWith("/auth/signup")
    && !path.startsWith("/auth/refresh");
}

async function tryRefreshSession(): Promise<boolean> {
  if (isRefreshing) {
    return new Promise((resolve) => {
      refreshQueue.push(resolve);
    });
  }

  isRefreshing = true;
  try {
    const res = await fetch(getApiUrl("/auth/refresh"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
    });
    const ok = res.ok;
    if (!ok) clearSession();
    refreshQueue.forEach((cb) => cb(ok));
    refreshQueue = [];
    return ok;
  } catch {
    clearSession();
    refreshQueue.forEach((cb) => cb(false));
    refreshQueue = [];
    return false;
  } finally {
    isRefreshing = false;
  }
}

export async function refreshAccessToken(): Promise<boolean> {
  return tryRefreshSession();
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  retry = true
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  const res = await fetch(getApiUrl(path), {
    ...options,
    headers,
    credentials: "include",
  });

  if (res.status === 401 && retry && shouldAttemptRefresh(path)) {
    const refreshed = await tryRefreshSession();
    if (refreshed) return request<T>(path, options, false);
    throw new Error("Session expired. Please log in again.");
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(err.detail || "Request failed");
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return res.json();
}

export const api = {
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, {
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    }),
  get: <T>(path: string) =>
    request<T>(path, { method: "GET" }),
  patch: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(body) }),
  delete: <T>(path: string) =>
    request<T>(path, { method: "DELETE" }),
};

export async function streamChat(
  message: string,
  conversationId: string | null,
  onChunk: (text: string) => void,
  onConvId: (id: string) => void,
  onDone: () => void,
  onError: (e: string) => void,
  retry = true
) {
  const res = await fetch(getApiUrl("/api/chat"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify({ message, conversation_id: conversationId }),
  });

  if (res.status === 401 && retry) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      await streamChat(message, conversationId, onChunk, onConvId, onDone, onError, false);
      return;
    }
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Chat failed" }));
    onError(err.detail || "Chat failed");
    return;
  }

  const reader = res.body?.getReader();
  if (!reader) {
    onError("Chat stream unavailable");
    return;
  }

  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        const sseLine = line.endsWith("\r") ? line.slice(0, -1) : line;
        if (!sseLine.startsWith("data: ")) continue;
        const data = sseLine.slice(6);
        if (!data) continue;
        if (data === "[DONE]") {
          onDone();
          continue;
        }
        if (data.startsWith('{"conversation_id"')) {
          try {
            onConvId(JSON.parse(data).conversation_id);
          } catch {
            // Ignore malformed metadata chunk and keep streaming content.
          }
          continue;
        }
        onChunk(data.replace(/\\n/g, "\n"));
      }
    }
  } catch (err) {
    console.warn("[streamChat] Stream ended:", err);
    onDone();
  } finally {
    reader.releaseLock();
  }
}
