const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

export function setTokens(accessToken: string, refreshToken?: string) {
  localStorage.setItem("access_token", accessToken);
  if (refreshToken) localStorage.setItem("refresh_token", refreshToken);
}

export function clearTokens() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("user");
}

export function getUser() {
  if (typeof window === "undefined") return null;
  const u = localStorage.getItem("user");
  return u ? JSON.parse(u) : null;
}

export function setUser(user: object) {
  localStorage.setItem("user", JSON.stringify(user));
}

// ─── Token refresh ─────────────────────────────────────────────────────
let isRefreshing = false;
let refreshQueue: Array<(token: string | null) => void> = [];

async function tryRefreshToken(): Promise<string | null> {
  const refreshToken = typeof window !== "undefined"
    ? localStorage.getItem("refresh_token")
    : null;
  if (!refreshToken) return null;

  if (isRefreshing) {
    return new Promise((resolve) => { refreshQueue.push(resolve); });
  }

  isRefreshing = true;
  try {
    const res = await fetch(`${API_URL}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if (!res.ok) {
      clearTokens();
      refreshQueue.forEach((cb) => cb(null));
      refreshQueue = [];
      if (typeof window !== "undefined") window.location.href = "/login";
      return null;
    }
    const data = await res.json();
    setTokens(data.access_token);
    if (data.user) setUser(data.user);
    refreshQueue.forEach((cb) => cb(data.access_token));
    refreshQueue = [];
    return data.access_token;
  } catch {
    clearTokens();
    refreshQueue.forEach((cb) => cb(null));
    refreshQueue = [];
    return null;
  } finally {
    isRefreshing = false;
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  retry = true
): Promise<T> {
  const token = getToken();

  // No token and not a POST → return empty silently
if (!token && options.method !== "POST") {
  return [] as unknown as T;
}


  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });

  // Auto-refresh on 401
  if (res.status === 401 && retry) {
    const newToken = await tryRefreshToken();
    if (newToken) return request<T>(path, options, false);
    if (options.method === "GET") return [] as unknown as T;
    throw new Error("Session expired. Please log in again.");
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(err.detail || "Request failed");
  }
  return res.json();
}

export const api = {
  post: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "POST", body: JSON.stringify(body) }),
  get: <T>(path: string) =>
    request<T>(path, { method: "GET" }),        // ← explicitly pass GET
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
  onError: (e: string) => void
) {
  const token = getToken();
  const res = await fetch(`${API_URL}/api/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ message, conversation_id: conversationId }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Chat failed" }));
    onError(err.detail || "Chat failed");
    return;
  }

const reader = res.body!.getReader();
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
      const trimmed = line.trim();
      if (!trimmed.startsWith("data: ")) continue;
      const data = trimmed.slice(6);
      if (!data) continue;
      if (data === "[DONE]") { onDone(); continue; }
      if (data.startsWith('{"conversation_id"')) {
        try { onConvId(JSON.parse(data).conversation_id); } catch {}
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
