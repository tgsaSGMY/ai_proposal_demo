import { ref, onMounted } from "vue";
import mammoth from "mammoth";

let pdfjsLib: any = null;

async function loadPdfJs() {
  if (pdfjsLib) {
    return pdfjsLib;
  }
  try {
    // @ts-expect-error: pdfjs-dist/build/pdf doesn't have type declarations
    const pdfjsModule = await import("pdfjs-dist/build/pdf");
    pdfjsLib = pdfjsModule;
    console.log("pdfjsLib version:", pdfjsLib.version);
    // 設置 worker 路徑 - 使用本地 node_modules 中的 worker 文件
    if (pdfjsLib.GlobalWorkerOptions) {
      // 使用相對路徑指向 node_modules 中的 worker
      const workerPath = new URL(
        "pdfjs-dist/build/pdf.worker.min.mjs",
        import.meta.url
      ).href;
      pdfjsLib.GlobalWorkerOptions.workerSrc = workerPath;
    }
    return pdfjsLib;
  } catch (error) {
    console.error("Failed to load pdf.js library:", error);
    throw new Error("Failed to load PDF library");
  }
}

export function useFileExtractor() {
  const isPdfReady = ref(false);

  onMounted(async () => {
    try {
      await loadPdfJs();
      isPdfReady.value = true;
    } catch (error) {
      console.error("Error loading PDF library:", error);
    }
  });

  /**
   * 從 Word 或 PDF 檔案中提取文字
   */
  async function extractTextFromFile(file: File): Promise<string> {
    if (file.type === "application/pdf") {
      if (!pdfjsLib) {
        throw new Error(
          "PDF library is not loaded yet. Please try again in a moment."
        );
      }
      const arrayBuffer = await file.arrayBuffer();
      const pdf = await pdfjsLib.getDocument(arrayBuffer).promise;
      let textContent = "";
      for (let i = 1; i <= pdf.numPages; i++) {
        const page = await pdf.getPage(i);
        const text = await page.getTextContent();
        textContent +=
          text.items.map((item: any) => item.str).join(" ") + "\n\n";
      }
      return textContent;
    } else if (
      file.type ===
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ) {
      const arrayBuffer = await file.arrayBuffer();
      const result = await mammoth.extractRawText({ arrayBuffer });
      return result.value;
    } else {
      throw new Error("不支援的檔案格式，請選擇 Word (.docx) 或 PDF 檔案。");
    }
  }

  return {
    isPdfReady,
    extractTextFromFile,
  };
}
