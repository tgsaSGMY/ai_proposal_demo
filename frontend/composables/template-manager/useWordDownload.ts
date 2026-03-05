interface UseWordDownloadOptions {
  generateDocxDocument: () => Promise<Blob>;
  getFileName: () => string;
  notifyError: (message: string) => void;
}

export function useWordDownload(options: UseWordDownloadOptions) {
  async function handleDownloadWord() {
    try {
      const blob = await options.generateDocxDocument();

      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = options.getFileName();
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (err) {
      options.notifyError(
        `下載失敗: ${err instanceof Error ? err.message : "未知錯誤"}`,
      );
    }
  }

  return {
    handleDownloadWord,
  };
}
