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
    json_schema: Optional[Dict[str, Any]] = None
    system_prompt: Optional[str] = None
    critic_prompt: Optional[str] = None
    rewrite_prompt: Optional[str] = None
    custom_prompt_list: Optional[List[str]] = []

class TemplateConfig(BaseModel):
    """代表一個計畫書模板（Template）的配置，它包含多個章節。"""
    id: str
    grant_id: str
    name: str
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
    user_id: str = Field(..., description="發起請求的用戶 ID，用於配額和日誌記錄。")
    grant: str = Field(..., description="目標計畫書的 ID。")
    template: str = Field(..., description="目標模板的 ID。")
    user_input: str = Field(..., description="用戶提供的核心需求或主題。")
    sections: List[SectionGenerateRequest] = Field(..., description="需要生成的章節列表。")
    num_candidates: int = Field(2, ge=1, le=3)

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
    """生成合成數據（Synthetic Data）的請求。"""
    mode: str = Field(..., description="生成模式，'random'（隨機主題）或 'reverse'（從已有輸出反推輸入）。")
    grant_name: str
    template_name: str
    section_name: str
    json_output: Optional[Dict[str, Any]] = Field(None, description="在 'reverse' 模式下，提供已有的 JSON 輸出。")
    dynamic_fields_schema: Optional[List[DynamicFieldSchema]] = Field(None, description="定義動態輸入字段的結構。")

class ScrapeRequest(BaseModel):
    """"抓取網上資料請求"""
    url: str
    context_keywords: Optional[str] = ""

class BatchSyntheticRequest(BaseModel):
    '''批量生成請求'''
    count: int = Field(..., gt=0, le=20) # 限制一次最多生成 20 个
    grant_id: str
    template_id: str

# --- 5. 路由與管理模型 (Routing & Administration Models) ---
class RoutingRule(BaseModel):
    """定義一個模型路由規則，用於決定哪個請求應該由哪個模型處理。"""
    grant_id: Optional[str] = None
    section_id: Optional[str] = None
    template_id: Optional[str] = None
    model_id: str
    priority: int = Field(20, description="規則優先級，數字越小優先級越高。")
    description: Optional[str] = None

# --- 定義 source_type 的可用選項 ---
class UpdateSectionSettingsRequest(BaseModel):
    prompts: List[str]
    system_prompt: Optional[str] = None


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