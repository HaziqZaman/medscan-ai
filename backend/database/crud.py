from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import func

from database.models import User, AnalysisCase, ChatSession, ChatMessage
from api.schemas import AnalysisCaseCreate


def create_user(db: Session, name: str, email: str, password_hash: str):
    new_user = User(
        name=name,
        email=email,
        password_hash=password_hash,
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
            AnalysisCase.user_id == user_id,
        )
        .first()
    )


def get_latest_analysis_case_by_user(db: Session, user_id: int):
    return (
        db.query(AnalysisCase)
        .filter(AnalysisCase.user_id == user_id)
        .order_by(AnalysisCase.created_at.desc())
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
            AnalysisCase.prediction_label == "IDC",
        )
        .scalar()
        or 0
    )

    non_idc = (
        db.query(func.count(AnalysisCase.id))
        .filter(
            AnalysisCase.user_id == user_id,
            AnalysisCase.prediction_label == "Non-IDC",
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
        "recent_analyses": recent_analyses,
    }


# -----------------------------
# CHATBOT CRUD
# -----------------------------

def create_chat_session(db: Session, user_id: int, title: str = "New Chat"):
    new_session = ChatSession(
        user_id=user_id,
        title=title,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session


def get_chat_session_by_id_and_user(db: Session, session_id: int, user_id: int):
    return (
        db.query(ChatSession)
        .filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id,
        )
        .first()
    )


def get_chat_sessions_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 50):
    return (
        db.query(ChatSession)
        .filter(ChatSession.user_id == user_id)
        .order_by(ChatSession.updated_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
def delete_chat_session_by_id_and_user(db: Session, session_id: int, user_id: int) -> bool:
    session = (
        db.query(ChatSession)
        .filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id,
        )
        .first()
    )

    if not session:
        return False

    db.delete(session)
    db.commit()
    return True


def delete_recent_chat_sessions_by_user(
    db: Session,
    user_id: int,
    limit: int = 5,
) -> int:
    recent_sessions = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == user_id)
        .order_by(ChatSession.updated_at.desc())
        .limit(limit)
        .all()
    )

    deleted_count = 0
    for session in recent_sessions:
        db.delete(session)
        deleted_count += 1

    db.commit()
    return deleted_count


def update_chat_session_timestamp(db: Session, session_id: int):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if session:
        session.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(session)
    return session


def update_chat_session_title(db: Session, session_id: int, title: str):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if session:
        session.title = title
        session.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(session)
    return session


def create_chat_message(
    db: Session,
    session_id: int,
    role: str,
    content: str,
    related_case_id: int | None = None,
    sources_json: list | None = None,
):
    new_message = ChatMessage(
        session_id=session_id,
        role=role,
        content=content,
        related_case_id=related_case_id,
        sources_json=sources_json,
        created_at=datetime.utcnow(),
    )
    db.add(new_message)

    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if session:
        session.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(new_message)
    return new_message


def get_chat_messages_by_session(db: Session, session_id: int, user_id: int):
    session = get_chat_session_by_id_and_user(db, session_id, user_id)
    if not session:
        return []

    return (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )


def create_or_get_chat_session(
    db: Session,
    user_id: int,
    session_id: int | None = None,
    default_title: str = "New Chat",
):
    if session_id is not None:
        existing_session = get_chat_session_by_id_and_user(db, session_id, user_id)
        if existing_session:
            return existing_session

    return create_chat_session(db=db, user_id=user_id, title=default_title)


def generate_chat_title_from_message(message: str) -> str:
    if not message:
        return "New Chat"

    cleaned = " ".join(message.strip().split())
    if len(cleaned) <= 40:
        return cleaned

    return cleaned[:40].rstrip() + "..."


def build_case_summary(case: AnalysisCase | None) -> str | None:
    if not case:
        return None

    extra_data = case.extra_data or {}

    def safe(value, fallback="N/A"):
        return value if value not in (None, "", []) else fallback

    lines = [
        f"Case ID: {case.id}",
        f"Model: {safe(case.model_type)}",
        f"Result: {safe(case.prediction_label)}",
        f"Confidence: {safe(case.confidence)}",
    ]

    if case.model_type == "model_a":
        if extra_data.get("note"):
            lines.append(f"Note: {extra_data.get('note')}")

    elif case.model_type == "model_b":
        combined = extra_data.get("combined_result", {}) or {}
        b1 = (extra_data.get("b1_result", {}) or {}).get("findings", {}) or {}
        b2 = (extra_data.get("b2_result", {}) or {}).get("findings", {}) or {}

        if combined.get("grade_support"):
            lines.append(f"Grade Support: {combined.get('grade_support')}")

        if b1.get("nuclei_density"):
            lines.append(f"Nuclei Density: {b1.get('nuclei_density')}")

        if b2.get("mitotic_activity_level"):
            lines.append(f"Mitotic Activity: {b2.get('mitotic_activity_level')}")

    return "\n".join(lines)
def delete_all_chat_sessions_by_user(db: Session, user_id: int) -> int:
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == user_id)
        .all()
    )

    deleted_count = 0
    for session in sessions:
        db.delete(session)
        deleted_count += 1

    db.commit()
    return deleted_count
    if not case:
        return None

    extra_data = case.extra_data or {}

    lines = [
        f"Case ID: {case.id}",
        f"Model Type: {case.model_type}",
        f"Prediction: {case.prediction_label or 'N/A'}",
        f"Confidence: {case.confidence if case.confidence is not None else 'N/A'}",
        f"Inference Time: {case.inference_time if case.inference_time is not None else 'N/A'}",
        f"Result Status: {case.result_status}",
        f"Created At: {case.created_at}",
    ]

    if case.heatmap_path:
        lines.append("Heatmap: Available")

    if case.model_type == "model_a":
        if extra_data.get("original_filename"):
            lines.append(f"Original File: {extra_data.get('original_filename')}")
        if extra_data.get("note"):
            lines.append(f"Note: {extra_data.get('note')}")

    elif case.model_type == "model_b":
        combined = extra_data.get("combined_result", {}) or {}
        b1 = (extra_data.get("b1_result", {}) or {}).get("findings", {}) or {}
        b2 = (extra_data.get("b2_result", {}) or {}).get("findings", {}) or {}

        if combined.get("grade_support"):
            lines.append(f"Grade Support: {combined.get('grade_support')}")
        if combined.get("summary"):
            lines.append(f"Combined Summary: {combined.get('summary')}")

        if b1.get("nuclei_count") is not None:
            lines.append(f"B1 Nuclei Count: {b1.get('nuclei_count')}")
        if b1.get("nuclei_density"):
            lines.append(f"B1 Nuclei Density: {b1.get('nuclei_density')}")
        if b1.get("irregularity_score") is not None:
            lines.append(f"B1 Irregularity Score: {b1.get('irregularity_score')}")

        if b2.get("predicted_mitosis_count") is not None:
            lines.append(f"B2 Predicted Mitosis Count: {b2.get('predicted_mitosis_count')}")
        if b2.get("mitotic_activity_level"):
            lines.append(f"B2 Mitotic Activity Level: {b2.get('mitotic_activity_level')}")

    return "\n".join(lines)