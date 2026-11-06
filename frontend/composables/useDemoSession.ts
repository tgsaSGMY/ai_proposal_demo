// Single source of the visitor's demo session.
//
// GET /demo is the ONLY endpoint that mints the session id + sets the cookie
// (every other endpoint uses the read-only `require_demo_session_id` dependency
// on the backend). It must therefore be called exactly once per page load:
// multiple callers (the page, the layout, useCurrentUser) hitting it in parallel
// before the Set-Cookie lands each mint a SEPARATE session, so the id the
// frontend keeps for the register `ref` diverges from the cookie the chat
// WebSocket uses — leaving the conversation in one demo row and the claim
// pointed at a different, empty one.
//
// Memoising the request guarantees a single mint shared by every caller. The
// promise is created synchronously on the first call, so concurrent callers all
// await the same in-flight request rather than starting their own.
let demoSessionPromise: Promise<Record<string, any> | null> | null = null;
// The session id returned by GET /demo. Sent as X-Demo-Session-Id on later API
// calls so they still work when the browser drops the cookie (frontend and API
// on different hosts, e.g. localhost vs 127.0.0.1). The chat WebSocket already
// sends the same id as ?session_id=.
let demoSessionId = "";

export function getDemoSessionId(): string {
  return demoSessionId;
}

// fetch() for demo-session-scoped endpoints: includes the cookie and the
// X-Demo-Session-Id header fallback.
export function demoFetch(input: string, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers || {});
  if (demoSessionId && !headers.has("X-Demo-Session-Id")) {
    headers.set("X-Demo-Session-Id", demoSessionId);
  }
  return fetch(input, { credentials: "include", ...init, headers });
}

export function useDemoSession() {
  const ensureDemoSession = (): Promise<Record<string, any> | null> => {
    if (typeof window === "undefined") return Promise.resolve(null);
    if (!demoSessionPromise) {
      const config = useRuntimeConfig();
      const apiBaseUrl = `${config.public.apiBaseUrl}/api`;
      demoSessionPromise = fetch(`${apiBaseUrl}/demo`, { credentials: "include" })
        .then((resp) => {
          if (resp.status === 429) {
            return {
              _error: "RATE_LIMITED",
              _retry_after: resp.headers.get("Retry-After") || "0",
            };
          }
          return resp.ok ? resp.json() : null;
        })
        .then((data) => {
          if (data && typeof data.session_id === "string") {
            demoSessionId = data.session_id;
          }
          return data;
        })
        .catch((err) => {
          console.error("Failed to bootstrap demo session", err);
          demoSessionPromise = null; // allow a retry after a transient failure
          return null;
        });
    }
    return demoSessionPromise;
  };

  return { ensureDemoSession };
}
