from datetime import datetime
from typing import Optional, Any, List, Dict

from pydantic import BaseModel, Field


class AnalysisCaseBase(BaseModel):
    user_id: Optional[int] = None
    model_type: str
    image_path: str
    prediction_label: Optional[str] = None
    confidence: Optional[float] = None
    result_status: str = "completed"
    heatmap_path: Optional[str] = None
    inference_time: Optional[float] = None
    extra_data: Optional[Any] = None


class AnalysisCaseCreate(AnalysisCaseBase):
    pass


class AnalysisCaseResponse(AnalysisCaseBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# -----------------------------
# CHATBOT SCHEMAS
# -----------------------------

class ChatQueryRequest(BaseModel):
    message: str
    session_id: Optional[int] = None
    case_id: Optional[int] = None
    use_latest_case: bool = False


class ChatQueryResponse(BaseModel):
    answer: str
    session_id: int
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    used_case_summary: Optional[str] = None


class ChatSessionResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChatMessageResponse(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    related_case_id: Optional[int] = None
    sources_json: Optional[Any] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatHistoryResponse(BaseModel):
    session_id: int
    title: str
    messages: List[ChatMessageResponse] = Field(default_factory=list)


class ExplainLatestCaseRequest(BaseModel):
    session_id: Optional[int] = None
    message: str = "Explain my latest case in simple educational terms."