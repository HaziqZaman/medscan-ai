import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]   # backend/

# .env ko import time par hi load karo
load_dotenv(BASE_DIR / ".env")

RAG_DIR = BASE_DIR / "rag"
STORAGE_DIR = BASE_DIR / "storage"
DOCS_DIR = STORAGE_DIR / "docs" / "medical_sources"
INDEX_DIR = STORAGE_DIR / "indexes"

CHUNKS_PATH = INDEX_DIR / "chunks.jsonl"
MANIFEST_PATH = INDEX_DIR / "documents_manifest.json"
BM25_PATH = INDEX_DIR / "bm25_index.json"
VECTOR_PATH = INDEX_DIR / "vector_index.json"

ALLOWED_EXTENSIONS = {".txt", ".md", ".pdf", ".html", ".htm"}

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_GENERATION_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")

CHUNK_SIZE_WORDS = int(os.getenv("RAG_CHUNK_SIZE_WORDS", "220"))
CHUNK_OVERLAP_WORDS = int(os.getenv("RAG_CHUNK_OVERLAP_WORDS", "40"))

EMBEDDING_DIMENSION = int(os.getenv("RAG_EMBEDDING_DIMENSION", "768"))
EMBEDDING_BATCH_SIZE = int(os.getenv("RAG_EMBEDDING_BATCH_SIZE", "16"))

TOP_K_RETRIEVAL = int(os.getenv("RAG_TOP_K_RETRIEVAL", "12"))
TOP_K_RERANKED = int(os.getenv("RAG_TOP_K_RERANKED", "6"))

SUPPORTED_SOURCE_PREFIXES = {
    "nci",
    "who",
    "cdc",
    "nhs",
    "acs",
    "medlineplus",
    "ncbi",
}


def ensure_directories() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_DIR.mkdir(parents=True, exist_ok=True)