import json
from typing import Dict, List

import numpy as np
from dotenv import load_dotenv

from rag.config import (
    BASE_DIR,
    CHUNKS_PATH,
    VECTOR_PATH,
    ensure_directories,
)

LOCAL_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
LOCAL_EMBEDDING_DIMENSION = 384
LOCAL_EMBEDDING_BATCH_SIZE = 32
LOCAL_EMBEDDING_DEVICE = "cpu"

_embedding_model = None


def load_chunk_records() -> List[Dict]:
    if not CHUNKS_PATH.exists():
        raise FileNotFoundError(f"Chunks file not found: {CHUNKS_PATH}")

    records: List[Dict] = []
    with CHUNKS_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def normalize_vector(values: List[float]) -> List[float]:
    vector = np.array(values, dtype=np.float32)
    norm = np.linalg.norm(vector)
    if norm == 0:
        return vector.tolist()
    return (vector / norm).tolist()


def get_embedding_model():
    global _embedding_model

    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "Local embeddings require sentence-transformers. "
                "Install it with: pip install sentence-transformers torch"
            ) from exc

        _embedding_model = SentenceTransformer(
            LOCAL_EMBEDDING_MODEL,
            device=LOCAL_EMBEDDING_DEVICE,
        )

    return _embedding_model


def embed_texts(texts: List[str], task_type: str = "RETRIEVAL_DOCUMENT") -> List[List[float]]:
    if not texts:
        return []

    model = get_embedding_model()

    vectors = model.encode(
        texts,
        batch_size=LOCAL_EMBEDDING_BATCH_SIZE,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    return [np.asarray(vector, dtype=np.float32).tolist() for vector in vectors]


def embed_query(query: str) -> List[float]:
    vectors = embed_texts([query], task_type="RETRIEVAL_QUERY")
    return vectors[0]


def build_vector_index() -> Dict:
    records = load_chunk_records()
    texts = [record["text"] for record in records]

    vectors = embed_texts(texts, task_type="RETRIEVAL_DOCUMENT")

    vector_records = []
    for record, embedding in zip(records, vectors):
        vector_records.append(
            {
                "chunk_id": record["chunk_id"],
                "document_id": record["document_id"],
                "text": record["text"],
                "metadata": record["metadata"],
                "embedding": embedding,
            }
        )

    return {
        "model": LOCAL_EMBEDDING_MODEL,
        "dimension": LOCAL_EMBEDDING_DIMENSION,
        "count": len(vector_records),
        "records": vector_records,
    }


def save_vector_index(index_data: Dict) -> None:
    with VECTOR_PATH.open("w", encoding="utf-8") as f:
        json.dump(index_data, f, ensure_ascii=False)


def main() -> None:
    load_dotenv(BASE_DIR / ".env")
    ensure_directories()

    print("Building vector index from chunk records...")
    index_data = build_vector_index()
    save_vector_index(index_data)

    print("Vector index complete.")
    print(f"Saved to: {VECTOR_PATH}")
    print(f"Total vectors: {index_data['count']}")
    print(f"Embedding model: {index_data['model']}")
    print(f"Embedding dimension: {index_data['dimension']}")


if __name__ == "__main__":
    main()