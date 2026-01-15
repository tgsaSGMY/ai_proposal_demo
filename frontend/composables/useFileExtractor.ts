// ===== 导入依赖库 =====
// 导入 Vue 响应式 API 和生命周期钩子
import { ref, onMounted } from "vue";

// ===== Mammoth 库（Word 文件解析）=====
// 缓存已加载的 mammoth 模块，避免重复加载
let mammothModule: any = null;

/**
 * 动态加载 mammoth 库
 * mammoth 用于从 Word (.docx) 文件中提取文本内容
 *
 * 特点：
 *   - 只在首次调用时加载，之后使用缓存
 *   - 只在客户端加载（防止服务器端错误）
 *   - 通过动态 import 实现，减少初始包大小
 */
async function loadMammoth() {
  // 如果已经加载过，直接返回缓存的模块
  if (mammothModule) return mammothModule;

  // 防止在服务器端加载（服务器端不需要解析文件）
  if (process.server) {
    throw new Error("mammoth should not be loaded on server");
  }

  // 动态导入 mammoth 库
  const mod = await import("mammoth");
  // 保存模块到缓存（处理 CommonJS 和 ES Module 的兼容性）
  mammothModule = mod.default || mod;
  return mammothModule;
}

// ===== PDF.js 库（PDF 文件解析）=====
// 缓存已加载的 pdf.js 库，避免重复加载
let pdfjsLib: any = null;

/**
 * 动态加载 PDF.js 库
 * PDF.js 用于从 PDF 文件中提取文本内容
 *
 * 特点：
 *   - 只在首次调用时加载，之后使用缓存
 *   - 需要配置 worker 路径（PDF.js 使用 Web Worker 进行处理）
 *   - 通过动态 import 实现，减少初始包大小
 *
 * 返回值：
 *   - 成功：返回 pdf.js 库对象
 *   - 失败：抛出错误
 */
async function loadPdfJs() {
  // 如果已经加载过，直接返回缓存的库
  if (pdfjsLib) {
    return pdfjsLib;
  }

  try {
    // ===== 导入 PDF.js 库 =====
    // 注意：TypeScript 不知道 pdfjs-dist 的类型，所以使用 @ts-expect-error 来忽略错误
    // @ts-expect-error: pdfjs-dist/build/pdf 没有 TypeScript 类型声明
    const pdfjsModule = await import("pdfjs-dist/build/pdf");
    // 保存到缓存
    pdfjsLib = pdfjsModule;

    // ===== 配置 PDF.js Worker 路径 =====
    // PDF.js 使用 Web Worker 在后台线程处理 PDF，所以需要指定 worker 文件的位置
    if (pdfjsLib.GlobalWorkerOptions) {
      // 使用相对路径指向 node_modules 中的 worker 文件
      // 这样 PDF.js 知道在哪里找到 worker 脚本
      const workerPath = new URL(
        "pdfjs-dist/build/pdf.worker.min.mjs",
        import.meta.url
      ).href;
      pdfjsLib.GlobalWorkerOptions.workerSrc = workerPath;
    }
    return pdfjsLib;
  } catch (error) {
    // 如果加载失败，打印错误并抛出异常
    console.error("Failed to load pdf.js library:", error);
    throw new Error("Failed to load PDF library");
  }
}

// ===== 文件提取器组合式函数 =====
/**
 * 用于从 Word (.docx) 和 PDF 文件中提取文本内容
 *
 * 功能：
 *   - 动态加载必要的库（mammoth for Word, pdf.js for PDF）
 *   - 支持 Word (.docx) 文件
 *   - 支持 PDF 文件
 *   - 提供 PDF 库加载状态
 */
export function useFileExtractor() {
  // ===== PDF 库加载状态 =====
  // 用于追踪 PDF 库是否已加载完成
  // 某些操作可能需要等待 PDF 库准备好
  const isPdfReady = ref(false);

  // ===== 组件挂载时的初始化 =====
  // 在组件挂载时预先加载 PDF.js 库，以加快后续使用时的响应速度
  onMounted(async () => {
    try {
      // 预加载 PDF.js 库
      await loadPdfJs();
      // 标记 PDF 库已准备好
      isPdfReady.value = true;
    } catch (error) {
      // 如果加载失败，打印错误但不中断程序
      // （用户上传非 PDF 文件时不受影响）
      console.error("Error loading PDF library:", error);
    }
  });

  // ===== 文件文本提取核心方法 =====
  /**
   * 从 Word 或 PDF 文件中提取文本
   *
   * 支持的文件格式：
   *   - Word: .docx（application/vnd.openxmlformats-officedocument.wordprocessingml.document）
   *   - PDF: .pdf（application/pdf）
   *
   * 参数：file - 用户上传的文件对象
   *
   * 返回值：
   *   - 成功：提取出的文本内容（字符串）
   *   - 失败：抛出错误
   *
   * 工作流程：
   *   1. 检查文件类型（PDF 或 Word）
   *   2. 根据文件类型加载相应的库
   *   3. 使用库提取文本内容
   *   4. 返回提取结果
   */
  async function extractTextFromFile(file: File): Promise<string> {
    // ===== 处理 PDF 文件 =====
    if (file.type === "application/pdf") {
      // 检查 PDF.js 库是否已加载
      if (!pdfjsLib) {
        throw new Error(
          "PDF library is not loaded yet. Please try again in a moment."
        );
      }

      // 读取文件为 ArrayBuffer（二进制数据）
      const arrayBuffer = await file.arrayBuffer();
      // 使用 PDF.js 加载 PDF 文档
      const pdf = await pdfjsLib.getDocument(arrayBuffer).promise;
      // 用于存储所有页面的文本
      let textContent = "";

      // 遍历 PDF 的每一页进行文本提取
      for (let i = 1; i <= pdf.numPages; i++) {
        // 获取第 i 页
        const page = await pdf.getPage(i);
        // 获取页面的文本内容对象
        const text = await page.getTextContent();
        // 将页面中的文本项目拼接成字符串，项目之间用空格分隔
        // 每一页后面添加两个换行符作为页面分隔
        textContent +=
          text.items.map((item: any) => item.str).join(" ") + "\n\n";
      }
      return textContent;
    }
    // ===== 处理 Word 文件 =====
    else if (
      file.type ===
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ) {
      // 读取文件为 ArrayBuffer（二进制数据）
      const arrayBuffer = await file.arrayBuffer();
      // 加载 mammoth 库
      const mammoth = await loadMammoth();
      // 使用 mammoth 从 Word 文档中提取纯文本（不包含格式）
      const result = await mammoth.extractRawText({ arrayBuffer });
      // 返回提取出的文本
      return result.value;
    }
    // ===== 不支持的文件格式 =====
    else {
      throw new Error("不支援的檔案格式，請選擇 Word (.docx) 或 PDF 檔案。");
    }
  }

  // ===== 导出公共 API =====
  // 返回 PDF 加载状态和文本提取方法
  return {
    isPdfReady, // PDF.js 库是否已加载（响应式数据）
    extractTextFromFile, // 从文件中提取文本的方法
  };
}
