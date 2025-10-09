# Pydantic 模型用於 FastAPI 的請求和響應驗證。
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

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


# model_rebuild() 会在类定义完后刷新它们的 forward references，让 Pydantic 正确解析嵌套关系。
GrantConfig.model_rebuild()
TemplateConfig.model_rebuild()