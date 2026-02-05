// ===== 导入依赖库 =====
// 导入 mammoth 库用于从 Word 文件中提取文本
import mammoth from "mammoth";
import { supabase } from "~/utils/supabaseClient";

// ===== Word 文件文本提取 =====

/**
 * 从 Word 文档中提取纯文本
 *
 * 功能：
 *   - 读取 .docx 文件的二进制内容
 *   - 使用 mammoth 库提取文本（不包含格式）
 *   - 返回提取出的纯文本内容
 *
 * 参数：
 *   - file: 用户上传的 Word 文件对象
 *
 * 返回值：
 *   - Promise<string>: 提取出的纯文本内容
 *
 * 说明：
 *   - mammoth 只提取文本内容，不保留格式（粗体、颜色等）
 *   - 这对于后端 AI 处理是最合适的
 */
export async function extractTextFromWord(file: File): Promise<string> {
  // 将 File 对象转换为 ArrayBuffer（二进制数据）
  const arrayBuffer = await file.arrayBuffer();
  // 使用 mammoth 提取纯文本内容
  const result = await mammoth.extractRawText({ arrayBuffer });
  // 返回提取出的文本
  return result.value;
}

// ===== 自动填充 API 调用 =====

/**
 * 调用后端自动填充 API
 *
 * 功能：
 *   - 将提取的 Word 文本发送到后端
 *   - 后端 AI 会根据 Schema 信息自动填充各个字段
 *   - 返回后端生成的填充结果
 *
 * 工作流程：
 *   1. 构建请求 payload
 *   2. 添加 main_idea 对象（用于提取计划名称和摘要）
 *   3. 将原始 sections 放在后面
 *   4. 添加 prompt_mode 标记为 "word_import"
 *   5. 发送 POST 请求到后端 API
 *   6. 等待后端响应并返回结果
 *
 * 参数：
 *   - payload: 请求载荷，包含：
 *     * document_text: 从 Word 提取的文本
 *     * sections: 当前的动态字段结构
 *     * user_id: 当前用户 ID
 *   - apiBaseUrl: 后端 API 的基础 URL
 *
 * 返回值：
 *   - Promise<Record<string, any>>: 后端返回的填充结果
 *     格式：{
 *       "section_id": {
 *         "content": {
 *           "field_key": "填充的文本内容"
 *         }
 *       }
 *     }
 *
 * 错误处理：
 *   - 如果 API 返回错误，抛出包含错误信息的异常
 */
export async function callAutoFillApi(
  payload: {
    document_text: string; // 从 Word 提取的文本内容
    sections: Array<{
      // 动态字段结构
      section_id: string;
      section_name: string;
      json_schema: Record<string, any>;
    }>;
    user_id: string; // 当前用户 ID
  },
  apiBaseUrl: string, // 后端 API 基础 URL
): Promise<Record<string, any>> {
  // ===== 构建请求 Payload =====
  // 添加 main_idea 对象（用于后端生成计划名称和摘要）
  const mainIdea = {
    section_id: "main_idea",
    section_name: "Main Idea",
    json_schema: {
      type: "object",
      properties: {
        project_name_and_summary: {
          type: "string",
          description: "項目名稱和總結摘要",
        },
      },
      required: ["project_name_and_summary"],
    },
  };

  // 在所有 sections 之前添加 main_idea，确保后端首先处理
  const updatedSections = [mainIdea, ...payload.sections];
  // 创建更新后的 payload
  const updatedPayload = {
    ...payload,
    sections: updatedSections,
    prompt_mode: "word_import", // 标记这是 Word 导入模式
  };

  // ===== 获取认证令牌 =====
  const {
    data: { session },
  } = await supabase.auth.getSession();
  const token = session?.access_token || "";

  // ===== 发送 API 请求 =====
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${apiBaseUrl}/autofill_from_document`, {
    method: "POST",
    headers,
    body: JSON.stringify(updatedPayload),
  });

  // ===== 处理 API 响应 =====
  if (!response.ok) {
    // 如果响应失败，尝试读取错误信息
    const errorData = await response.json();
    throw new Error(errorData.detail || "後端處理失敗");
  }
  // 返回成功的响应
  return await response.json();
}

// ===== JSON Schema 构建工具 =====

/**
 * 为动态章节构建 JSON Schema
 *
 * 功能：
 *   - 根据字段信息生成 JSON Schema
 *   - 后端 AI 使用此 Schema 来生成结构化的回复
 *
 * 参数：
 *   - section: 动态章节对象，包含 fields 数组
 *
 * 返回值：
 *   - Record<string, any>: JSON Schema 对象
 *     包含 type、properties、required 等标准 JSON Schema 字段
 *
 * 说明：
 *   - 每个字段都定义为字符串类型（因为我们处理文本）
 *   - 所有字段都添加到 required 数组（后端会尽量填充）
 *   - Schema 遵循 JSON Schema 标准格式
 */
export function buildSectionSchema(section: {
  fields: Array<{
    propertyKey: string;
  }>;
}): Record<string, any> {
  // 初始化 Schema 对象
  const schema: {
    type: string;
    properties: { [key: string]: any };
    required: string[];
  } = {
    type: "object", // 这是一个对象
    properties: {}, // 对象的属性
    required: [], // 必需的属性列表
  };

  // 遍历所有字段并添加到 Schema
  section.fields.forEach((field) => {
    // 为每个字段添加属性定义
    schema.properties[field.propertyKey] = {
      type: "string",
      description: field.propertyKey,
    };
    // 将字段标记为必需
    schema.required.push(field.propertyKey);
  });

  return schema;
}

// ===== 后端响应处理 =====

/**
 * 处理后端返回的自动填充结果
 *
 * 功能：
 *   - 解析后端返回的填充结果
 *   - 将结果映射到对应的动态字段
 *   - 调用更新函数填充数据
 *
 * 工作流程：
 *   1. 验证响应格式是否有效
 *   2. 遍历每个章节
 *   3. 对每个字段提取后端返回的值
 *   4. 处理多种可能的响应格式（字符串、对象、嵌套等）
 *   5. 调用更新函数和展开函数
 *
 * 参数：
 *   - filledContent: 后端返回的填充结果
 *   - dynamicSections: 当前的动态字段结构
 *   - updateDynamicValue: 更新字段值的回调函数
 *   - ensureFieldExpanded: 确保字段展开的回调函数（用于 UI）
 *
 * 说明：
 *   - 会自动忽略无法解析的字段（静默跳过）
 *   - 只填充非空的值
 *   - 填充前会进行 trim（去除首尾空格）
 *
 * 错误处理：
 *   - 如果响应格式完全无效，抛出错误
 *   - 部分字段无法解析时，继续处理其他字段
 */
export function processAutoFillResults(
  filledContent: Record<string, any>,
  dynamicSections: Array<{
    sectionId: string;
    fields: Array<{
      propertyKey: string;
    }>;
  }>,
  updateDynamicValue: (
    sectionId: string,
    propertyKey: string,
    value: string,
  ) => void,
  ensureFieldExpanded: (sectionId: string, propertyKey: string) => void,
): void {
  // ===== 验证响应格式 =====
  if (!filledContent || typeof filledContent !== "object") {
    throw new Error("無效的後端回應格式");
  }

  // ===== 处理每个章节的填充结果 =====
  // 遍历每个动态章节
  dynamicSections.forEach((section) => {
    // 从响应中获取该章节的内容
    const sectionContent = filledContent[section.sectionId];
    // 如果该章节没有返回内容，则跳过
    if (!sectionContent || typeof sectionContent !== "object") {
      return;
    }

    // ===== 处理每个字段的填充结果 =====
    // 遍历该章节的所有字段
    section.fields.forEach((field) => {
      // 获取该字段的原始内容
      const rawFieldContent = sectionContent.content[field.propertyKey];
      // 如果字段内容为空，则跳过
      if (rawFieldContent === undefined || rawFieldContent === null) {
        return;
      }

      // ===== 解析字段值 =====
      let value: string | null = null;

      // 如果是字符串类型，直接使用
      if (typeof rawFieldContent === "string") {
        value = rawFieldContent;
      }
      // 如果是对象，尝试从中提取字符串值
      else if (
        typeof rawFieldContent === "object" &&
        rawFieldContent !== null
      ) {
        // 首先检查是否有 reply 字段
        if (typeof rawFieldContent.reply === "string") {
          value = rawFieldContent.reply;
        } else {
          // 否则获取对象中的第一个非空字符串值
          const firstStringEntry = Object.values(rawFieldContent).find(
            (entry) => typeof entry === "string" && entry.trim() !== "",
          );
          if (typeof firstStringEntry === "string") {
            value = firstStringEntry;
          }
        }
      }

      // ===== 填充数据 =====
      // 只有值非空时才进行填充
      if (value && value.trim() !== "") {
        // 调用更新函数填充值
        updateDynamicValue(section.sectionId, field.propertyKey, value.trim());
        // 确保字段在 UI 上展开（便于用户查看）
        ensureFieldExpanded(section.sectionId, field.propertyKey);
      }
    });
  });
}
