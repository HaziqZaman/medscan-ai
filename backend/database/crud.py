from sqlalchemy.orm import Session
from sqlalchemy import func

from database.models import User, AnalysisCase
from api.schemas import AnalysisCaseCreate


def create_user(db: Session, name: str, email: str, password_hash: str):
    new_user = User(
        name = name,
        email=email,
        password_hash=password_hash
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def create_analysis_case(db: Session, case_data: AnalysisCaseCreate):
    new_case = AnalysisCase(**case_data.model_dump())
    db.add(new_case)
    db.commit()
    db.refresh(new_case)
    return new_case


def get_analysis_cases_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return (
        db.query(AnalysisCase)
        .filter(AnalysisCase.user_id == user_id)
        .order_by(AnalysisCase.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_analysis_case_by_id_and_user(db: Session, case_id: int, user_id: int):
    return (
        db.query(AnalysisCase)
        .filter(
            AnalysisCase.id == case_id,
            AnalysisCase.user_id == user_id
        )
        .first()
    )


def get_dashboard_summary_by_user(db: Session, user_id: int):
    total_analyses = (
        db.query(func.count(AnalysisCase.id))
        .filter(AnalysisCase.user_id == user_id)
        .scalar()
        or 0
    )

    idc_detected = (
        db.query(func.count(AnalysisCase.id))
        .filter(
            AnalysisCase.user_id == user_id,
            AnalysisCase.prediction_label == "IDC"
        )
        .scalar()
        or 0
    )

    non_idc = (
        db.query(func.count(AnalysisCase.id))
        .filter(
            AnalysisCase.user_id == user_id,
            AnalysisCase.prediction_label == "Non-IDC"
        )
        .scalar()
        or 0
    )

    avg_confidence = (
        db.query(func.avg(AnalysisCase.confidence))
        .filter(AnalysisCase.user_id == user_id)
        .scalar()
    )
    avg_confidence = round(float(avg_confidence), 2) if avg_confidence is not None else 0.0

    recent_analyses = (
        db.query(AnalysisCase)
        .filter(AnalysisCase.user_id == user_id)
        .order_by(AnalysisCase.created_at.desc())
        .limit(5)
        .all()
    )

    return {
        "total_analyses": total_analyses,
        "idc_detected": idc_detected,
        "non_idc": non_idc,
        "avg_confidence": avg_confidence,
        "recent_analyses": recent_analyses
    }