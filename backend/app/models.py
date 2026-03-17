# 定義模型，確保類型是正確的
# Pydantic 模型用於 FastAPI 的請求和響應驗證。
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal 

# --- 1. 核心配置模型 (Core Configuration Models) ---
# 這些模型定義了應用程式最核心的數據結構，如計畫書、模板和章節。
class SectionConfig(BaseModel):
    """代表一個章節（Section）的完整配置信息。"""
    id: str
    template_id: str
    grant_id: str
    name: str
    current_version: Optional[int] = None
    json_schema: Optional[Dict[str, Any]] = None
    system_prompt: Optional[str] = None
    critic_prompt: Optional[str] = None
    rewrite_prompt: Optional[str] = None
    custom_prompt_list: Optional[List[str]] = []
    search_external: bool = True

class TemplateConfig(BaseModel):
    """代表一個計畫書模板（Template）的配置，它包含多個章節。"""
    id: str
    grant_id: str
    name: str
    subtitle: Optional[str] = None
    description: Optional[str] = None
    logo_storage_path: Optional[str] = None
    iconBg: Optional[str] = None
    isOpen: Optional[bool] = None
    word_export_config: Optional[List[Dict[str, Any]]] = None
    name_recommend_config: Optional[Dict[str, Any]] = None
    sections: List[SectionConfig] = []

class GrantConfig(BaseModel):
    """代表一個計畫書（Grant）的頂層配置，它包含多個模板。"""
    id: str
    name: str
    templates: List[TemplateConfig] = []

# model_rebuild() 会在类定义完后刷新它们的 forward references，让 Pydantic 正确解析嵌套关系。
GrantConfig.model_rebuild()
TemplateConfig.model_rebuild()

# --- 2. 主要生成流程模型 (Main Generation Flow Models) ---
# 這些模型用於核心的「內容生成」API 端點。
class SectionGenerateRequest(BaseModel):
    """在一次生成請求中，指定要生成的單個章節。"""
    section_id: str

class GenerateRequest(BaseModel):
    """發起內容生成流程的請求體。"""
    grant: str = Field(..., description="目標計畫書的 ID。")
    template: str = Field(..., description="目標模板的 ID。")
    user_input: str = Field(..., description="用戶提供的核心需求或主題。")
    num_candidates: int = Field(2, ge=1, le=3)
    is_external: bool = Field(True, description="是否使用外部模型（True）還是內部模型（False）。")
    selected_model: Optional[str] = Field(None, description="可選的指定模型，如 'gpt-5.2', 'gpt-5.1' 等。如果設置，將跳過模型路由。")
    project_id: Optional[str] = Field(None, description="專案 ID，用於圖片生成時的關聯。")


class PlanRevisionRequest(BaseModel):
    """基於既有版本重新優化計畫書的請求。"""

    grant: str = Field(..., description="目標計畫書的 ID。")
    template: str = Field(..., description="目標模板的 ID。")
    current_version: Dict[str, Any] = Field(
        ..., description="目前版本的內容，按照 section_id 映射。"
    )
    stored_answer: Optional[Dict[str, Any]] = Field(
        default=None, description="已儲存的問答或使用者輸入摘要。"
    )
    project_title: Optional[str] = Field(
        default="", description="專案名稱，提供額外上下文。"
    )
    project_summary: Optional[str] = Field(
        default="", description="專案摘要，提供額外上下文。"
    )
    num_candidates: int = Field(2, ge=1, le=3)
    is_external: bool = Field(True, description="是否使用外部模型。")
    selected_model: Optional[str] = Field(
        default=None, description="可選的指定模型 ID。"
    )
    project_id: Optional[str] = Field(
        default=None, description="專案 ID，便於記錄。"
    )

class SectionGenerateResponse(BaseModel):
    """單個章節生成的響應結果。"""
    section_id: str
    content: Optional[str] = Field(None, description="生成的格式化文本內容（如果適用）。")
    raw_json_content: Optional[Dict[str, Any]] = Field(None, description="生成的原始 JSON 對象。")
    error: Optional[str] = Field(None, description="如果生成失敗，則包含錯誤信息。")


# --- 3. 數據集管理模型 (Dataset Management Models) ---
# 用於創建、讀取、更新和刪除（CRUD）數據集條目。
SourceType = Literal["actor_critic", "external_direct", "golden_samples", "synthetic_data"]
class DatasetEntry(BaseModel):
    """代表一條標準的數據集記錄。"""
    source_type: SourceType = Field(..., description="數據來源，如 'synthetic_data', 'golden_samples', 'actor_critic'。")
    grant_id: str
    template_id: str
    section_id: str
    prompt: str
    final_answer: Dict[str, Any]
    rejected_answer: Optional[Dict[str, Any]] = None

class SaveDatasetRequest(BaseModel):
    """用於批量保存數據集條目的請求，每個條目可以有不同的來源。"""
    entries: List[DatasetEntry]

# --- 4. 合成數據與提示生成 (Synthetic Data & Prompt Generation) ---
# 用於自動生成訓練數據或用戶輸入的相關模型。
class DynamicFieldSchema(BaseModel):
    """描述一個動態生成的輸入字段，用於合成數據。"""
    label: str = Field(..., description="給用戶看的問題或標籤，例如 '我們的目標客戶是誰？'")

class SyntheticInputRequest(BaseModel):
    """生成合成數據（Synthetic Data）的請求。
    
    支持兩種模式：
    - 'random': 根據補助主題隨機生成新的用戶輸入
    - 'reverse': 根據計畫書內容反推摘要和動態字段
    """
    mode: str = Field(..., description="生成模式，'random'（隨機主題）或 'reverse'（從計畫書反推）。")
    grant_name: str = Field(..., description="補助主題名稱")
    template_name: str = Field(..., description="模板名稱")
    section_name: str = Field(..., description="章節名稱")
    # 在 reverse 模式下使用：計畫書內容用於反推
    plan_content: Optional[Dict[str, Any]] = Field(None, description="在 'reverse' 模式下，提供計畫書內容以反推動態字段。")
    # dynamic_fields_schema 必須提供，包含所有動態字段的標籤和定義
    dynamic_fields_schema: List[DynamicFieldSchema] = Field(..., description="定義動態輸入字段的結構（所有模式都使用），包含字段標籤。")
    user_id: str = Field(..., description="發起請求的用戶 ID，用於配額和日誌記錄。")


class ChatGuidanceHistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatGuidanceQuestion(BaseModel):
    id: str
    label: str
    prompt: str


class ChatGuidanceRequest(BaseModel):
    grant_id: str
    template_id: str
    grant_name: Optional[str] = None
    template_name: Optional[str] = None
    question: ChatGuidanceQuestion
    answers: Dict[str, str] = Field(default_factory=dict)
    history: List[ChatGuidanceHistoryMessage] = Field(
        default_factory=list,
        description="最近的對話歷史，將作為語境提供給 AI。",
    )


class ChatGuidanceResponse(BaseModel):
    question_id: str
    message: str


# --- 5. 路由與管理模型 (Routing & Administration Models) ---
class RoutingRule(BaseModel):
    """定義一個模型路由規則，用於決定哪個請求應該由哪個模型處理。"""
    grant_id: Optional[str] = None
    section_id: Optional[str] = None
    template_id: Optional[str] = None
    model_id: str
    priority: int = Field(20, description="規則優先級，數字越小優先級越高。")
    description: Optional[str] = None
    is_external: Optional[bool] = None

# --- 定義 source_type 的可用選項 ---
class UpdateSectionSettingsRequest(BaseModel):
    grant_id: str
    template_id: str
    custom_prompt_list: List[str]
    system_prompt: Optional[str] = None
    search_external: Optional[bool] = None

# --- 6. 其他特定 API 模型 (Other Specific API Models) ---
class SectionSchemaInfo(BaseModel):
    """在 AutoFill 請求中，傳遞單個章節的 ID、名稱和 Schema。"""
    section_id: str
    section_name: str
    json_schema: Dict[str, Any]

class AutoFillRequest(BaseModel):
    """根據一份完整的文檔，自動填充多個章節的內容。"""
    document_text: str
    sections: List[SectionSchemaInfo]
    prompt_mode: str = "default"  # "default" 或 "word_import" - word_import 针对从 Word 文件导入进行优化

class GenerateFieldContentRequest(BaseModel):
    """基於已填寫欄位生成單個欄位內容的請求。"""
    field_title: str = Field(..., description="欄位名稱")
    field_description: str = Field("", description="欄位說明")
    subfield_label: str = Field(..., description="子欄位標籤")
    current_value: str = Field("", description="欄位當前值")
    filled_fields: Dict[str, str] = Field(default_factory=dict, description="已填寫的其他欄位（標籤 -> 內容）")
    plan_name: str = Field("", description="計畫名稱")
    plan_summary: str = Field("", description="計畫摘要")


# --- 7. Builder 管理頁面模型 (Template Manager) ---
class GrantCreateRequest(BaseModel):
    """建立新的 Grant 記錄。"""
    id: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=255)


class GrantUpdateRequest(BaseModel):
    """更新既有 Grant 記錄，允許局部欄位。"""
    id: Optional[str] = Field(None, min_length=1, max_length=64)
    name: Optional[str] = Field(None, min_length=1, max_length=255)


class PlanTemplateCreateRequest(BaseModel):
    """建立新的計畫模板。"""
    id: str = Field(..., min_length=1, max_length=64)
    grant_id: str = Field(..., min_length=1, max_length=64)
    order: Optional[int] = Field(default=None, ge=0)
    name: str = Field(..., min_length=1, max_length=255)
    subtitle: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    logo_storage_path: Optional[str] = None
    iconBg: Optional[str] = Field(default="#F8FAFC")
    isOpen: bool = True
    word_export_config: Optional[List[Dict[str, Any]]] = None
    name_recommend_config: Optional[Dict[str, Any]] = None


class PlanTemplateUpdateRequest(BaseModel):
    """更新既有計畫模板，允許局部更新。"""
    id: Optional[str] = Field(None, min_length=1, max_length=64)
    grant_id: Optional[str] = Field(None, min_length=1, max_length=64)
    order: Optional[int] = Field(default=None, ge=0)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    subtitle: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    logo_storage_path: Optional[str] = None
    iconBg: Optional[str] = None
    isOpen: Optional[bool] = None
    word_export_config: Optional[List[Dict[str, Any]]] = None
    name_recommend_config: Optional[Dict[str, Any]] = None


class SectionBaseRequest(BaseModel):
    """章節共用欄位。"""
    name: str = Field(..., min_length=1, max_length=255)
    order: int = Field(0, ge=0, description="章節顯示順序，數字越小越前面。")
    json_schema: Optional[Dict[str, Any]] = Field(
        default=None, description="章節使用的 JSON Schema"
    )


class SectionCreateRequest(SectionBaseRequest):
    """建立新的章節。"""
    id: str = Field(..., min_length=1, max_length=128)
    grant_id: str = Field(..., min_length=1, max_length=64)
    template_id: str = Field(..., min_length=1, max_length=64)


class SectionUpdateRequest(BaseModel):
    """更新既有章節，允許局部更新。"""
    id: Optional[str] = Field(None, min_length=1, max_length=128)
    grant_id: Optional[str] = Field(None, min_length=1, max_length=64)
    template_id: Optional[str] = Field(None, min_length=1, max_length=64)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    order: Optional[int] = Field(None, ge=0)
    json_schema: Optional[Dict[str, Any]] = Field(default=None)