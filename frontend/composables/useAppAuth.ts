import { supabase } from "~/utils/supabaseClient";

interface AppSession {
  isAuthenticated: boolean;
  accessToken: string | null;
  provider: "supabase" | "external" | null;
}

async function hardLogoutAndRedirect(): Promise<void> {
  try {
    await supabase.auth.signOut();
  } catch {
    // Ignore and continue logout cleanup.
  }

  try {
    const config = useRuntimeConfig();
    const API_BASE_URL = `${config.public.apiBaseUrl}/api`;
    await fetch(`${API_BASE_URL}/external-auth/logout`, {
      method: "POST",
      credentials: "include",
    });
  } catch {
    // Ignore logout endpoint failures; redirect anyway.
  }

  if (typeof window !== "undefined") {
    window.location.href = "/login";
  }
}

export async function getAppSession(): Promise<AppSession> {
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (session?.access_token && session?.user) {
    return {
      isAuthenticated: true,
      accessToken: session.access_token,
      provider: "supabase",
    };
  }

  const config = useRuntimeConfig();
  const API_BASE_URL = `${config.public.apiBaseUrl}/api`;
  const response = await fetch(`${API_BASE_URL}/auth/status`, {
    method: "GET",
    credentials: "include",
  });

  if (response.ok) {
    const statusPayload = (await response.json().catch(() => ({}))) as {
      authenticated?: boolean;
      provider?: "supabase" | "external" | null;
    };

    if (statusPayload.authenticated) {
      return {
        isAuthenticated: true,
        accessToken: null,
        provider: statusPayload.provider || "external",
      };
    }

    return {
      isAuthenticated: false,
      accessToken: null,
      provider: null,
    };
  }

  return {
    isAuthenticated: false,
    accessToken: null,
    provider: null,
  };
}

export async function authenticatedFetch(
  input: string,
  init: RequestInit = {},
): Promise<Response> {
  const appSession = await getAppSession();
  if (!appSession.isAuthenticated) {
    await hardLogoutAndRedirect();
    throw new Error("Unauthenticated session");
  }

  const headers = new Headers(init.headers || {});
  if (appSession.accessToken) {
    headers.set("Authorization", `Bearer ${appSession.accessToken}`);
  }

  const response = await fetch(input, {
    ...init,
    headers,
    credentials: "include",
  });

  if (response.status === 401) {
    await hardLogoutAndRedirect();
  }

  return response;
}

export async function appLogout(): Promise<void> {
  await hardLogoutAndRedirect();
}
