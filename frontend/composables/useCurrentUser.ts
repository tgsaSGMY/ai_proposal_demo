// Demo build: "current user" is the cookie-issued demo session.
// Read the demo_session_id from /api/demo and expose it as userId so
// pages that read `userId.value` (e.g. for Realtime channel scoping)
// keep working.

import type { Ref } from "vue";

interface UseCurrentUserResult {
  userId: Ref<string | null>;
  isFetchingUser: Ref<boolean>;
  refreshUser: (force?: boolean) => Promise<string | null>;
}

export function useCurrentUser(): UseCurrentUserResult {
  const userId = useState<string | null>("currentUserId", () => null);
  const isFetchingUser = useState<boolean>("currentUserIdLoading", () => false);

  const refreshUser = async (_force = false): Promise<string | null> => {
    if (typeof window === "undefined") return null;
    if (isFetchingUser.value) return userId.value;
    isFetchingUser.value = true;
    try {
      const config = useRuntimeConfig();
      const apiBaseUrl = `${config.public.apiBaseUrl}/api`;
      const response = await fetch(`${apiBaseUrl}/demo`, { credentials: "include" });
      if (response.ok) {
        const row = await response.json();
        userId.value = row?.session_id ?? null;
      } else {
        userId.value = null;
      }
    } catch (error) {
      console.error("Failed to load demo session id", error);
      userId.value = null;
    } finally {
      isFetchingUser.value = false;
    }
    return userId.value;
  };

  return { userId, isFetchingUser, refreshUser };
}
