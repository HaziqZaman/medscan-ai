from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.routes import auth
from api.routes import user
from api.routes import predict
from api.routes import cases
from api.routes import chatbot
from api.routes import explain
from api.routes import admin

from database.db import engine
from database import models

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="MedScan AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parents[1]
STORAGE_DIR = BASE_DIR / "storage"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/storage", StaticFiles(directory=STORAGE_DIR), name="storage")

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(user.router, prefix="/user", tags=["User"])
app.include_router(predict.router, prefix="/analysis", tags=["Analysis"])
app.include_router(cases.router, prefix="/cases", tags=["Cases"])
app.include_router(chatbot.router, prefix="/chatbot", tags=["Chatbot"])
app.include_router(explain.router, prefix="/explain", tags=["Explainability"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])