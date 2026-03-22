import { supabase } from "~/utils/supabaseClient";

// 前端可辨識的登入狀態模型：支援 Supabase 與外部登入兩種來源。
interface AppSession {
  isAuthenticated: boolean;
  accessToken: string | null;
  provider: "supabase" | "external" | null;
}

// 統一組出後端 API 根路徑，避免重複拼接字串。
function getApiBaseUrl(): string {
  const config = useRuntimeConfig();
  return `${config.public.apiBaseUrl}/api`;
}

// 強制登出流程：先清 Supabase，再呼叫後端外部登入登出，最後導向登入頁。
async function hardLogoutAndRedirect(): Promise<void> {
  try {
    await supabase.auth.signOut();
  } catch {
    // Ignore and continue logout cleanup.
  }

  // Forcefully clear Supabase local storage tokens in case signOut failed
  if (typeof window !== "undefined") {
    for (const key of Object.keys(localStorage)) {
      if (key.startsWith("sb-") && key.endsWith("-auth-token")) {
        localStorage.removeItem(key);
      }
    }
  }

  try {
    const apiBaseUrl = getApiBaseUrl();
    await fetch(`${apiBaseUrl}/external-auth/logout`, {
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

// 取得目前 App Session：優先檢查 Supabase，若無再檢查外部登入 cookie 狀態。
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

  const apiBaseUrl = getApiBaseUrl();
  const response = await fetch(`${apiBaseUrl}/auth/status`, {
    method: "GET",
    credentials: "include",
    cache: "no-store",
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

  // 未登入或驗證失敗時回傳統一的匿名狀態。
  return {
    isAuthenticated: false,
    accessToken: null,
    provider: null,
  };
}

// 包裝 fetch：自動附帶憑證與 Bearer token，若 401 則執行強制登出。
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

// 對外提供的登出 API，統一走強制登出流程。
export async function appLogout(): Promise<void> {
  await hardLogoutAndRedirect();
}
