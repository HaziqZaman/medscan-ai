from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from datetime import datetime
from database.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String,  nullable=False)

    email = Column(String, unique=True, index=True, nullable=False)

    password_hash = Column(String, nullable=False)

    role = Column(String, default="user")

    created_at = Column(DateTime, default=datetime.utcnow)

class AnalysisCase(Base):
    __tablename__ = "analysis_cases"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)  # keep nullable for now

    model_type = Column(String, nullable=False, index=True)
    image_path = Column(String, nullable=False)

    prediction_label = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    result_status = Column(String, nullable=False, default="completed")

    heatmap_path = Column(String, nullable=True)
    inference_time = Column(Float, nullable=True)

    extra_data = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)