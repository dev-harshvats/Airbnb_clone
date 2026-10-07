import type { ApiErrorBody, AuthResponse } from "@/types/api";

const BASE = "/api/v1";
const REFRESH_PATH = "/auth/refresh";
const REFRESH_LOCK = "airbnb-refresh";

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    readonly detail: string,
  ) {
    super(detail);
  }
}

/**
 * The client knows nothing about the auth store (Dependency Inversion): whoever owns the session
 * plugs these hooks in once at start-up, and tests plug in fakes.
 */
type SessionHooks = {
  getToken: () => string | null;
  onRefreshed: (session: AuthResponse) => void;
  onSessionLost: () => void;
};

let hooks: SessionHooks = { getToken: () => null, onRefreshed() {}, onSessionLost() {} };

export function configureApi(next: Partial<SessionHooks>) {
  hooks = { ...hooks, ...next };
}

export type ApiInit = Omit<RequestInit, "body"> & {
  body?: unknown; // objects are sent as JSON; FormData is sent as-is
  query?: Record<string, string | number | boolean | undefined | null | (string | number)[]>;
};

function buildUrl(path: string, query: ApiInit["query"]) {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query ?? {})) {
    for (const item of Array.isArray(value) ? value : [value]) {
      if (item !== undefined && item !== null && item !== "") params.append(key, String(item));
    }
  }
  const qs = params.toString();
  return `${BASE}${path}${qs ? `?${qs}` : ""}`;
}

async function toError(response: Response): Promise<ApiError> {
  const body = (await response.json().catch(() => null)) as Partial<ApiErrorBody> | null;
  return new ApiError(
    response.status,
    body?.code ?? "UNKNOWN",
    body?.detail ?? "Something went wrong. Please try again.",
  );
}

async function send(path: string, init: ApiInit): Promise<Response> {
  const { body, query, headers, ...rest } = init;
  const finalHeaders: Record<string, string> = { ...(headers as Record<string, string>) };
  const token = hooks.getToken();
  if (token) finalHeaders.Authorization = `Bearer ${token}`;
  let payload: BodyInit | undefined;
  if (body instanceof FormData) {
    payload = body; // the browser sets the multipart boundary itself
  } else if (body !== undefined) {
    finalHeaders["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }
  return fetch(buildUrl(path, query), { ...rest, headers: finalHeaders, body: payload });
}

let inflightRefresh: Promise<AuthResponse> | null = null;

async function runRefresh(): Promise<AuthResponse> {
  const response = await fetch(`${BASE}${REFRESH_PATH}`, { method: "POST" });
  if (!response.ok) throw await toError(response);
  const session = (await response.json()) as AuthResponse;
  hooks.onRefreshed(session);
  return session;
}

/**
 * Exchange the refresh cookie for a new access token.
 *
 * Calls are shared within a tab (several failing requests trigger one refresh). Across tabs a Web
 * Lock serialises them: the server rotates the cookie on every refresh and treats a replayed
 * cookie as theft, so two tabs refreshing at the same instant would otherwise log the user out.
 */
export function refreshSession(): Promise<AuthResponse> {
  if (!inflightRefresh) {
    // `request` resolves with the callback's result; awaiting it flattens the nested promise type.
    const run: Promise<AuthResponse> =
      typeof navigator !== "undefined" && navigator.locks
        ? (async () => await navigator.locks.request(REFRESH_LOCK, runRefresh))()
        : runRefresh();
    inflightRefresh = run.finally(() => {
      inflightRefresh = null;
    });
  }
  return inflightRefresh;
}

const isAuthPath = (path: string) => path.startsWith("/auth/");

export async function api<T = unknown>(path: string, init: ApiInit = {}): Promise<T> {
  let response = await send(path, init);

  // An expired access token: refresh once and replay the request.
  if (response.status === 401 && hooks.getToken() && !isAuthPath(path)) {
    const original = await toError(response);
    try {
      await refreshSession();
    } catch {
      hooks.onSessionLost();
      throw original;
    }
    response = await send(path, init);
  }

  if (!response.ok) throw await toError(response);
  return (response.status === 204 ? undefined : await response.json()) as T;
}
