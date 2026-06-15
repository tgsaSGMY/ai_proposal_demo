import { ref, onMounted, onUnmounted } from "vue";

export function useSessionExpiry(expiresAt: string | null) {
  const timeString = ref("");
  const isExpired = ref(false);
  let interval: ReturnType<typeof setInterval> | null = null;

  function update() {
    if (!expiresAt) {
      timeString.value = "";
      isExpired.value = false;
      return;
    }
    const now = Date.now();
    const expiry = new Date(expiresAt).getTime();
    const diff = expiry - now;

    if (diff <= 0) {
      timeString.value = "已過期";
      isExpired.value = true;
      if (interval) {
        clearInterval(interval);
        interval = null;
      }
      return;
    }

    isExpired.value = false;
    const days = Math.floor(diff / 86400000);
    const hours = Math.floor((diff % 86400000) / 3600000);
    const minutes = Math.floor((diff % 3600000) / 60000);
    const seconds = Math.floor((diff % 60000) / 1000);

    if (days > 0) {
      timeString.value = `${days}天 ${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
    } else {
      timeString.value = `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
    }
  }

  onMounted(() => {
    update();
    interval = setInterval(update, 1000);
  });

  onUnmounted(() => {
    if (interval) {
      clearInterval(interval);
      interval = null;
    }
  });

  return { timeString, isExpired };
}
