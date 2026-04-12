import json
from pathlib import Path
from typing import Dict, List

import numpy as np
from dotenv import load_dotenv

from rag.config import (
    BASE_DIR,
    CHUNKS_PATH,
    VECTOR_PATH,
    GEMINI_API_KEY,
    GEMINI_EMBEDDING_MODEL,
    EMBEDDING_DIMENSION,
    EMBEDDING_BATCH_SIZE,
    ensure_directories,
)


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


def chunked(items: List[str], batch_size: int):
    for start in range(0, len(items), batch_size):
        yield items[start:start + batch_size]


def get_genai_client():
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found. Check backend/.env")

    from google import genai
    return genai.Client(api_key=GEMINI_API_KEY)


def embed_texts(texts: List[str], task_type: str) -> List[List[float]]:
    if not texts:
        return []

    from google.genai import types

    client = get_genai_client()
    all_vectors: List[List[float]] = []

    for batch in chunked(texts, EMBEDDING_BATCH_SIZE):
        result = client.models.embed_content(
            model=GEMINI_EMBEDDING_MODEL,
            contents=batch,
            config=types.EmbedContentConfig(
                task_type=task_type,
                output_dimensionality=EMBEDDING_DIMENSION,
            ),
        )

        batch_vectors = [normalize_vector(item.values) for item in result.embeddings]
        all_vectors.extend(batch_vectors)

    return all_vectors


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
        "model": GEMINI_EMBEDDING_MODEL,
        "dimension": EMBEDDING_DIMENSION,
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