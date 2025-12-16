import type { Ref } from "vue";
import { supabase } from "~/utils/supabaseClient";

interface UseCurrentUserResult {
  userId: Ref<string | null>;
  isFetchingUser: Ref<boolean>;
  refreshUser: () => Promise<string | null>;
}

export function useCurrentUser(): UseCurrentUserResult {
  const userId = useState<string | null>("currentUserId", () => null);
  const isFetchingUser = useState<boolean>("currentUserIdLoading", () => false);

  const refreshUser = async (): Promise<string | null> => {
    if (typeof window === "undefined") {
      return null;
    }

    if (isFetchingUser.value) {
      return userId.value;
    }

    isFetchingUser.value = true;
    try {
      const {
        data: { session },
        error,
      } = await supabase.auth.getSession();

      if (error) {
        throw error;
      }

      userId.value = session?.user?.id ?? null;
    } catch (error) {
      console.error("Failed to load current user session", error);
      userId.value = null;
    } finally {
      isFetchingUser.value = false;
    }

    return userId.value;
  };

  return { userId, isFetchingUser, refreshUser };
}
