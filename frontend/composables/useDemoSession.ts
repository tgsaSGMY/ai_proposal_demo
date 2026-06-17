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

export function useDemoSession() {
  const ensureDemoSession = (): Promise<Record<string, any> | null> => {
    if (typeof window === "undefined") return Promise.resolve(null);
    if (!demoSessionPromise) {
      const config = useRuntimeConfig();
      const apiBaseUrl = `${config.public.apiBaseUrl}/api`;
      demoSessionPromise = fetch(`${apiBaseUrl}/demo`, { credentials: "include" })
        .then((resp) => (resp.ok ? resp.json() : null))
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
