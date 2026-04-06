from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel


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