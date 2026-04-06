from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from database.db import get_db
from database.crud import (
    get_analysis_cases_by_user,
    get_analysis_case_by_id_and_user,
    get_dashboard_summary_by_user,
)
from api.schemas import AnalysisCaseResponse

router = APIRouter()


@router.get("", response_model=List[AnalysisCaseResponse])
def get_cases(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return get_analysis_cases_by_user(db, current_user.id)


@router.get("/dashboard/summary")
def dashboard_summary(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    summary = get_dashboard_summary_by_user(db, current_user.id)

    recent_analyses_serialized = []
    for case in summary["recent_analyses"]:
        recent_analyses_serialized.append({
            "id": case.id,
            "user_id": case.user_id,
            "model_type": case.model_type,
            "image_path": case.image_path,
            "prediction_label": case.prediction_label,
            "confidence": case.confidence,
            "result_status": case.result_status,
            "heatmap_path": case.heatmap_path,
            "inference_time": case.inference_time,
            "extra_data": case.extra_data,
            "created_at": case.created_at,
        })

    return {
        "total_analyses": summary["total_analyses"],
        "idc_detected": summary["idc_detected"],
        "non_idc": summary["non_idc"],
        "avg_confidence": summary["avg_confidence"],
        "recent_analyses": recent_analyses_serialized,
    }


@router.get("/{case_id}", response_model=AnalysisCaseResponse)
def get_case_by_id(
    case_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    case = get_analysis_case_by_id_and_user(db, case_id, current_user.id)

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    return case