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
