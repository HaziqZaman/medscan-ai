from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    JSON,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import relationship

from database.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="user")
    created_at = Column(DateTime, default=datetime.utcnow)

    analysis_cases = relationship("AnalysisCase", back_populates="user")
    chat_sessions = relationship("ChatSession", back_populates="user")


class AnalysisCase(Base):
    __tablename__ = "analysis_cases"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    model_type = Column(String, nullable=False, index=True)
    image_path = Column(String, nullable=False)

    prediction_label = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    result_status = Column(String, nullable=False, default="completed")

    heatmap_path = Column(String, nullable=True)
    inference_time = Column(Float, nullable=True)

    extra_data = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="analysis_cases")
    chat_messages = relationship("ChatMessage", back_populates="related_case")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    title = Column(String, nullable=False, default="New Chat")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="chat_sessions")
    messages = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at.asc()",
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False, index=True)

    role = Column(String, nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)

    related_case_id = Column(Integer, ForeignKey("analysis_cases.id"), nullable=True)
    sources_json = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    session = relationship("ChatSession", back_populates="messages")
    related_case = relationship("AnalysisCase", back_populates="chat_messages")