import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, api, configureApi } from "@/lib/api/client";

const AUTH = { access_token: "fresh", token_type: "bearer", expires_in: 900, user: { id: 1 } };

function json(status: number, body: unknown) {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

let token: string | null;
const sessionLost = vi.fn();
const fetchMock = vi.fn<(url: string, init?: RequestInit) => Promise<Response>>();

function bearerOf(init?: RequestInit) {
  return (init?.headers as Record<string, string> | undefined)?.Authorization;
}

beforeEach(() => {
  token = "stale";
  sessionLost.mockReset();
  fetchMock.mockReset();
  vi.stubGlobal("fetch", fetchMock);
  configureApi({
    getToken: () => token,
    onRefreshed: (session) => {
      token = session.access_token;
    },
    onSessionLost: sessionLost,
  });
});

describe("api client", () => {
  it("sends the bearer token and turns {detail, code} bodies into ApiError", async () => {
    fetchMock.mockResolvedValueOnce(json(409, { detail: "Dates taken", code: "BOOKING_CONFLICT" }));

    const error = await api("/bookings", { method: "POST", body: { a: 1 } }).catch((e) => e);

    expect(bearerOf(fetchMock.mock.calls[0][1])).toBe("Bearer stale");
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ status: 409, code: "BOOKING_CONFLICT", detail: "Dates taken" });
  });

  it("refreshes an expired token and retries the request once", async () => {
    fetchMock
      .mockResolvedValueOnce(json(401, { detail: "expired", code: "INVALID_TOKEN" }))
      .mockResolvedValueOnce(json(200, AUTH)) // POST /auth/refresh
      .mockResolvedValueOnce(json(200, { ok: true }));

    await expect(api("/bookings")).resolves.toEqual({ ok: true });

    expect(fetchMock.mock.calls[1][0]).toBe("/api/v1/auth/refresh");
    expect(bearerOf(fetchMock.mock.calls[2][1])).toBe("Bearer fresh");
    expect(sessionLost).not.toHaveBeenCalled();
  });

  it("logs the user out when the refresh fails", async () => {
    fetchMock
      .mockResolvedValueOnce(json(401, { detail: "expired", code: "INVALID_TOKEN" }))
      .mockResolvedValueOnce(json(401, { detail: "gone", code: "INVALID_TOKEN" }));

    await expect(api("/bookings")).rejects.toMatchObject({ status: 401 });

    expect(sessionLost).toHaveBeenCalledOnce();
    expect(fetchMock).toHaveBeenCalledTimes(2); // the original call and one refresh, no retry
  });

  it("shares a single refresh between concurrent 401s", async () => {
    fetchMock.mockImplementation(async (url, init) => {
      if (url === "/api/v1/auth/refresh") return json(200, AUTH);
      return bearerOf(init) === "Bearer fresh"
        ? json(200, { ok: true })
        : json(401, { detail: "expired", code: "INVALID_TOKEN" });
    });

    await Promise.all([api("/bookings"), api("/wishlists"), api("/hosting/stats")]);

    const refreshes = fetchMock.mock.calls.filter(([url]) => url === "/api/v1/auth/refresh");
    expect(refreshes).toHaveLength(1);
  });
});
