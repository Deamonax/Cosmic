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
    if (typeof originalEnv === "undefined") {
      delete process.env.NEXT_PUBLIC_API_BASE_URL;
    } else {
      process.env.NEXT_PUBLIC_API_BASE_URL = originalEnv;
    }
  });

  it("calls fetch with the provided path", async () => {
    const mockJson = { ok: true };
    const mockResponse = {
      ok: true,
      status: 200,
      json: vi.fn().mockResolvedValue(mockJson),
      text: vi.fn().mockResolvedValue(JSON.stringify(mockJson)),
    } as unknown as Response;
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(mockResponse);

    const result = await apiFetch("/healthz");

    expect(fetchSpy).toHaveBeenCalledWith(
      "http://test.local/healthz",
      expect.objectContaining({
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
      }),
    );
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
      "Request to http://test.local/fail failed with status 500: Internal error"
    );
  });

  it("falls back to the browser origin when no env override is set", async () => {
    delete process.env.NEXT_PUBLIC_API_BASE_URL;
    const originalNodeEnv = process.env.NODE_ENV;
    process.env.NODE_ENV = "production";

    const origin = "https://frontend.example.com";
    const locationSpy = vi
      .spyOn(window, "location", "get")
      .mockReturnValue({
        origin,
        hostname: "frontend.example.com",
      } as Location);

    const mockResponse = {
      ok: true,
      status: 200,
      json: vi.fn(),
      text: vi.fn().mockResolvedValue("{\"ok\":true}"),
    } as unknown as Response;
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(mockResponse);

    await apiFetch("/healthz");

    expect(fetchSpy).toHaveBeenCalledWith(
      `${origin}/healthz`,
      expect.objectContaining({
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
      }),
    );

    locationSpy.mockRestore();
    process.env.NODE_ENV = originalNodeEnv;
  });
});
