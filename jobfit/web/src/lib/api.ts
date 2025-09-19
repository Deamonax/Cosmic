// web/src/lib/api.ts
export type FetchOptions = RequestInit & {
  parseJson?: boolean;
  timeoutMs?: number;
};

const defaultBaseUrl = "http://localhost:8000";

function isLocalHostname(hostname: string | undefined | null): boolean {
  if (!hostname) return false;
  return hostname === "localhost" || hostname === "127.0.0.1" || hostname === "[::1]";
}

function resolveBaseUrl(): string {
  const envBase = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
  if (envBase) {
    return envBase;
  }

  if (typeof window !== "undefined") {
    const { origin, hostname } = window.location ?? {};
    if (origin && origin !== "null") {
      const shouldUseOrigin = process.env.NODE_ENV === "production" || !isLocalHostname(hostname);
      if (shouldUseOrigin) {
        return origin;
      }
    }
  }

  return defaultBaseUrl;
}

function joinUrl(base: string, path: string) {
  const b = base.replace(/\/$/, "");
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${b}${p}`;
}

async function fetchWithTimeout(input: RequestInfo, init: RequestInit = {}, timeoutMs = 20_000) {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(input, { ...init, signal: controller.signal });
  } finally {
    clearTimeout(id);
  }
}

export async function apiFetch<T = unknown>(
  path: string,
  options: FetchOptions = {}
): Promise<T> {
  const baseUrl = resolveBaseUrl();
  const url = joinUrl(baseUrl, path);

  const {
    parseJson = true,
    timeoutMs = 20_000,
    headers,
    body,
    ...rest
  } = options;

  const res = await fetchWithTimeout(
    url,
    {
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        ...headers,
      },
      body: typeof body === "string" ? body : body ? JSON.stringify(body) : undefined,
      ...rest,
    },
    timeoutMs
  ).catch((err: any) => {
    // Network/CORS/timeout errors never have res.status
    const hint = err?.name === "AbortError" ? "Request timed out" : "Network/CORS error";
    throw new Error(`${hint} fetching ${url}: ${err?.message ?? err}`);
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    const detail = text.trim() || res.statusText || "Unknown error";
    throw new Error(`Request to ${url} failed with status ${res.status}: ${detail}`);
  }

  if (!parseJson) return undefined as unknown as T;

  // Gracefully handle empty body
  const text = await res.text();
  return (text ? JSON.parse(text) : ({} as T)) as T;
}

export async function postForm<T = unknown>(
  path: string,
  formData: FormData,
  timeoutMs = 60_000
): Promise<T> {
  const baseUrl = resolveBaseUrl();
  const url = joinUrl(baseUrl, path);

  const res = await fetchWithTimeout(
    url,
    {
      method: "POST",
      // Do NOT set Content-Type manually for FormData, the browser will set the boundary
      headers: { Accept: "application/json" },
      body: formData,
    },
    timeoutMs
  ).catch((err: any) => {
    const hint = err?.name === "AbortError" ? "Request timed out" : "Network/CORS error";
    throw new Error(`${hint} posting to ${url}: ${err?.message ?? err}`);
  });

  if (!res.ok) {
    const ct = res.headers.get("content-type") ?? "";
    let detail = "";
    try {
      if (ct.includes("application/json")) {
        const body = await res.json();
        detail =
          (typeof body?.detail === "string" && body.detail) ||
          (typeof body?.message === "string" && body.message) ||
          JSON.stringify(body);
      } else {
        detail = await res.text();
      }
    } catch {
      // ignore parse errors
    }
    throw new Error(`API ${res.status} ${res.statusText} at ${url}. ${detail || "No details"}`);
  }

  const ct = res.headers.get("content-type") ?? "";
  if (ct.includes("application/json")) {
    return (await res.json()) as T;
  }
  const text = await res.text();
  return text as unknown as T;
}
