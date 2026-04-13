from typing import List, Optional, Dict

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from database.db import get_db
from database.crud import (
    get_analysis_case_by_id_and_user,
    get_latest_analysis_case_by_user,
    create_or_get_chat_session,
    create_chat_message,
    get_chat_sessions_by_user,
    get_chat_messages_by_session,
    get_chat_session_by_id_and_user,
    update_chat_session_title,
    generate_chat_title_from_message,
    build_case_summary,
    delete_chat_session_by_id_and_user,
    delete_recent_chat_sessions_by_user,
)
from api.schemas import (
    ChatQueryRequest,
    ChatQueryResponse,
    ChatSessionResponse,
    ChatMessageResponse,
    ChatHistoryResponse,
    ExplainLatestCaseRequest,
)
from rag.answer_generator import generate_grounded_answer

router = APIRouter()

CASE_CONTEXT_HINTS = [
    "my latest case",
    "my case",
    "my previous result",
    "my analysis",
    "my last analysis",
    "my result",
    "latest case",
    "previous case",
]


def normalize_text(text: str) -> str:
    return " ".join(text.strip().lower().split())


def wants_case_context(text: str) -> bool:
    normalized = normalize_text(text)
    return any(phrase in normalized for phrase in CASE_CONTEXT_HINTS)


def get_case_context_for_request(
    db: Session,
    current_user_id: int,
    case_id: Optional[int],
    use_latest_case: bool,
    message: str,
):
    selected_case = None

    if case_id is not None:
        selected_case = get_analysis_case_by_id_and_user(
            db=db,
            case_id=case_id,
            user_id=current_user_id,
        )
        if not selected_case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Selected case not found for this user.",
            )

    elif use_latest_case or wants_case_context(message):
        selected_case = get_latest_analysis_case_by_user(
            db=db,
            user_id=current_user_id,
        )

    case_summary = build_case_summary(selected_case) if selected_case else None
    return selected_case, case_summary


@router.post("/query", response_model=ChatQueryResponse)
def query_chatbot(
    payload: ChatQueryRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    message = payload.message.strip()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty.",
        )

    session = create_or_get_chat_session(
        db=db,
        user_id=current_user.id,
        session_id=payload.session_id,
        default_title=generate_chat_title_from_message(message),
    )

    if session.title == "New Chat":
        update_chat_session_title(
            db=db,
            session_id=session.id,
            title=generate_chat_title_from_message(message),
        )

    selected_case, case_summary = get_case_context_for_request(
        db=db,
        current_user_id=current_user.id,
        case_id=payload.case_id,
        use_latest_case=payload.use_latest_case,
        message=message,
    )

    create_chat_message(
        db=db,
        session_id=session.id,
        role="user",
        content=message,
        related_case_id=selected_case.id if selected_case else None,
    )

    result = generate_grounded_answer(
        query=message,
        case_summary=case_summary,
    )

    answer = result["answer"]
    sources = result["sources"]

    create_chat_message(
        db=db,
        session_id=session.id,
        role="assistant",
        content=answer,
        related_case_id=selected_case.id if selected_case else None,
        sources_json=sources,
    )

    return ChatQueryResponse(
        answer=answer,
        session_id=session.id,
        sources=sources,
        used_case_summary=case_summary,
    )


@router.get("/history", response_model=List[ChatSessionResponse])
def get_chat_history_sessions(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    sessions = get_chat_sessions_by_user(db=db, user_id=current_user.id)
    return sessions


@router.delete("/history/recent", response_model=Dict[str, int])
def delete_recent_chats(
    limit: int = Query(5, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    deleted_count = delete_recent_chat_sessions_by_user(
        db=db,
        user_id=current_user.id,
        limit=limit,
    )

    return {
        "deleted_count": deleted_count,
    }


@router.get("/history/{session_id}", response_model=ChatHistoryResponse)
def get_chat_history_messages(
    session_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    session = get_chat_session_by_id_and_user(
        db=db,
        session_id=session_id,
        user_id=current_user.id,
    )
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found.",
        )

    messages = get_chat_messages_by_session(
        db=db,
        session_id=session_id,
        user_id=current_user.id,
    )

    return ChatHistoryResponse(
        session_id=session.id,
        title=session.title,
        messages=[ChatMessageResponse.model_validate(message) for message in messages],
    )


@router.delete("/history/{session_id}", response_model=Dict[str, str])
def delete_single_chat_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    deleted = delete_chat_session_by_id_and_user(
        db=db,
        session_id=session_id,
        user_id=current_user.id,
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found.",
        )

    return {
        "detail": "Chat session deleted successfully.",
    }


@router.post("/explain-latest-case", response_model=ChatQueryResponse)
def explain_latest_case(
    payload: ExplainLatestCaseRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    latest_case = get_latest_analysis_case_by_user(db=db, user_id=current_user.id)
    if not latest_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No analysis case found for this user.",
        )

    request_payload = ChatQueryRequest(
        message=payload.message,
        session_id=payload.session_id,
        case_id=latest_case.id,
        use_latest_case=True,
    )

    return query_chatbot(
        payload=request_payload,
        db=db,
        current_user=current_user,
    )