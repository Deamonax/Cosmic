export type FetchOptions = RequestInit & {
  parseJson?: boolean;
};

const defaultBaseUrl = "http://localhost:8000";

export async function apiFetch<T = unknown>(
  path: string,
  options: FetchOptions = {}
): Promise<T> {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? defaultBaseUrl;
  const { parseJson = true, headers, ...rest } = options;
  const response = await fetch(`${baseUrl}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...headers,
    },
    ...rest,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Request failed with status ${response.status}: ${text}`);
  }

  if (!parseJson) {
    return undefined as unknown as T;
  }

  return (await response.json()) as T;
}

export async function postForm<T = unknown>(
  path: string,
  formData: FormData
): Promise<T> {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? defaultBaseUrl;
  const response = await fetch(`${baseUrl}${path}`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const contentType = response.headers.get("content-type") ?? "";
    let message = `Request failed with status ${response.status}`;

    if (contentType.includes("application/json")) {
      try {
        const body = await response.json();
        message =
          (typeof body?.detail === "string" && body.detail) ||
          (typeof body?.message === "string" && body.message) ||
          JSON.stringify(body);
      } catch {
        // Ignore JSON parsing errors and fall back to default message.
      }
    } else {
      const text = await response.text();
      if (text) {
        message = text;
      }
    }

    throw new Error(message);
  }

  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    return (await response.json()) as T;
  }

  const text = await response.text();
  return text as unknown as T;
}
