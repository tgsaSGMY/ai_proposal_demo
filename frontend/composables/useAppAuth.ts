// Demo build: no auth. The shim preserves the parent platform's export
// surface so consumer pages (Chatbox, projects/[id].vue, etc.) keep
// compiling without per-callsite rewrites.
//
// - authenticatedFetch: plain fetch with credentials so the demo_session_id
//   cookie rides along.
// - getAppSession: returns an always-authenticated demo session.
// - appLogout: calls `DELETE /api/demo` to reset the visitor's row, then
//   reloads. Useful as a "start over" button.

interface AppSession {
  isAuthenticated: boolean;
  accessToken: string | null;
  provider: "demo";
}

function getApiBaseUrl(): string {
  const config = useRuntimeConfig();
  return `${config.public.apiBaseUrl}/api`;
}

export async function getAppSession(): Promise<AppSession> {
  return { isAuthenticated: true, accessToken: null, provider: "demo" };
}

export async function authenticatedFetch(
  input: string,
  init: RequestInit = {},
): Promise<Response> {
  return fetch(input, {
    ...init,
    credentials: "include",
  });
}

export async function appLogout(options?: { redirectTo?: string }): Promise<void> {
  try {
    await fetch(`${getApiBaseUrl()}/demo`, {
      method: "DELETE",
      credentials: "include",
    });
  } catch {
    // Reset is best-effort; we redirect regardless.
  }
  if (typeof window !== "undefined") {
    window.location.href = options?.redirectTo || "/";
  }
}
