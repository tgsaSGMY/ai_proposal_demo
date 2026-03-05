import { nextTick, onMounted, ref, watch } from "vue";

interface UseWordPreviewOptions {
  source: () => unknown;
  generatePreviewHtml: () => string;
  notifyError: (message: string) => void;
  debounceMs?: number;
}

export function useWordPreview(options: UseWordPreviewOptions) {
  const debounceMs = options.debounceMs ?? 800;

  const debouncedPreviewHtml = ref<string>("");
  const previewIframeRef = ref<HTMLIFrameElement | null>(null);
  const previewContainerRef = ref<HTMLDivElement | null>(null);

  let previewDebounceTimer: NodeJS.Timeout | null = null;
  let savedIframeScrollPosition = 0;

  function updatePreviewWithDebounce() {
    if (previewDebounceTimer) {
      clearTimeout(previewDebounceTimer);
    }

    previewDebounceTimer = setTimeout(() => {
      try {
        if (previewIframeRef.value && previewIframeRef.value.contentDocument) {
          const scrollElement =
            previewIframeRef.value.contentDocument.documentElement ||
            previewIframeRef.value.contentDocument.body;
          if (scrollElement) {
            savedIframeScrollPosition = scrollElement.scrollTop;
          }
        }

        debouncedPreviewHtml.value = options.generatePreviewHtml();
      } catch (error) {
        console.error("Error generating preview:", error);
      }
    }, debounceMs);
  }

  function handleIframeLoad() {
    if (
      previewIframeRef.value &&
      previewIframeRef.value.contentDocument &&
      savedIframeScrollPosition > 0
    ) {
      const scrollElement =
        previewIframeRef.value.contentDocument.documentElement ||
        previewIframeRef.value.contentDocument.body;
      if (scrollElement) {
        nextTick(() => {
          scrollElement.scrollTop = savedIframeScrollPosition;
        });
      }
    }
  }

  async function handlePreviewExport() {
    try {
      const previewHtml = options.generatePreviewHtml();
      const previewWindow = window.open("", "_blank");
      if (previewWindow) {
        previewWindow.document.write(previewHtml);
        previewWindow.document.close();
      } else {
        options.notifyError("無法開啟預覽視窗，請檢查瀏覽器設定");
      }
    } catch (err) {
      options.notifyError(
        `預覽生成失敗: ${err instanceof Error ? err.message : "未知錯誤"}`,
      );
    }
  }

  watch(
    options.source,
    () => {
      updatePreviewWithDebounce();
    },
    { deep: true },
  );

  onMounted(() => {
    debouncedPreviewHtml.value = options.generatePreviewHtml();
  });

  return {
    debouncedPreviewHtml,
    previewIframeRef,
    previewContainerRef,
    handleIframeLoad,
    handlePreviewExport,
    updatePreviewWithDebounce,
  };
}
