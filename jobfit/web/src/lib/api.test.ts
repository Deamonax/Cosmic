import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "./api";

declare let fetch: typeof globalThis.fetch;

describe("apiFetch", () => {
  const originalEnv = process.env.NEXT_PUBLIC_API_BASE_URL;

  beforeEach(() => {
    process.env.NEXT_PUBLIC_API_BASE_URL = "http://test.local";
  });

  afterEach(() => {
    vi.restoreAllMocks();
    process.env.NEXT_PUBLIC_API_BASE_URL = originalEnv;
  });

  it("calls fetch with the provided path", async () => {
    const mockJson = { ok: true };
    const mockResponse = {
      ok: true,
      status: 200,
      json: vi.fn().mockResolvedValue(mockJson),
      text: vi.fn(),
    } as unknown as Response;
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(mockResponse);

    const result = await apiFetch("/healthz");

    expect(fetchSpy).toHaveBeenCalledWith("http://test.local/healthz", {
      headers: {
        "Content-Type": "application/json",
      },
    });
    expect(result).toEqual(mockJson);
  });

  it("throws an error when the response is not ok", async () => {
    const mockResponse = {
      ok: false,
      status: 500,
      json: vi.fn(),
      text: vi.fn().mockResolvedValue("Internal error"),
    } as unknown as Response;
    vi.spyOn(globalThis, "fetch").mockResolvedValue(mockResponse);

    await expect(apiFetch("/fail")).rejects.toThrow(
      "Request failed with status 500: Internal error"
    );
  });
});
