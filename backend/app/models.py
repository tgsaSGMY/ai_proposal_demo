# Pydantic 模型用於 FastAPI 的請求和響應驗證。
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

# --- Pydantic Models ---
class SectionSchemaInfo(BaseModel):
    section_id: str
    section_name: str
    json_schema: Dict[str, Any]

class AutoFillRequest(BaseModel): 
    document_text: str
    sections: List[SectionSchemaInfo]
    
class DynamicFieldSchema(BaseModel):
    label: str # e.g., "我們的目標客戶是誰？"

class DatasetUpdateRequest(BaseModel):
    prompt: str
    final_answer: Dict[str, Any]
    
class SyntheticInputRequest(BaseModel):
    mode: str # 'random' or 'reverse'
    grant_name: str
    template_name: str
    section_name: str # 保持，用於 'reverse' 模式的上下文
    json_output: Optional[Dict[str, Any]] = None
    dynamic_fields_schema: Optional[List[DynamicFieldSchema]] = None # <-- 新增

class UpdatePromptsRequest(BaseModel):
    prompts: List[str]

class DatasetEntry(BaseModel):
    source_type: str # 'synthetic_data' or 'golden_samples'
    grant_id: str
    template_id: str
    section_id: str
    prompt: str
    final_answer: Dict[str, Any]

class SaveDatasetRequest(BaseModel):
    entries: List[DatasetEntry]

class BatchDatasetRequest(BaseModel):
    source_type: str  # 'golden_samples' or 'synthetic_data'
    entries: List[DatasetEntry]

class UserInputGenRequest(BaseModel):
    mode: str # 'synthetic' or 'golden'
    grant_id: str
    template_id: str
    # 'golden' 模式下，需要傳遞所有章節的結果
    outputs: Optional[Dict[str, Any]] = None 
    # 'synthetic' 模式下，可以傳遞一個主題
    topic: Optional[str] = "a typical SaaS business"

class SectionGenerateRequest(BaseModel):
    section_id: str

class GenerateRequest(BaseModel):
    user_id: str
    grant: str
    template: str
    user_input: str
    sections: List[SectionGenerateRequest] = Field(..., description="List of sections to generate")

class SectionGenerateResponse(BaseModel):
    section_id: str
    content: Optional[str] = None
    error: Optional[str] = None
    raw_json_content: Optional[Dict[str, Any]] = None 

class GrantConfig(BaseModel):
    id: str
    name: str
    templates: List['TemplateConfig'] = []

class TemplateConfig(BaseModel):
    id: str
    grant_id: str
    name: str
    sections: List['SectionConfig'] = []

class SectionConfig(BaseModel):
    id: str
    template_id: str
    grant_id: str
    name: str
    json_schema: Optional[Dict[str, Any]] = None
    system_prompt: Optional[str] = None
    critic_prompt: Optional[str] = None
    rewrite_prompt: Optional[str] = None
    custom_prompt_list: Optional[List[str]] = []

class RoutingRule(BaseModel):
    grant_id: Optional[str] = None
    section_id: Optional[str] = None
    template_id: Optional[str] = None
    model_id: str
    priority: int = 20
    description: Optional[str] = None


# model_rebuild() 会在类定义完后刷新它们的 forward references，让 Pydantic 正确解析嵌套关系。
GrantConfig.model_rebuild()
TemplateConfig.model_rebuild()