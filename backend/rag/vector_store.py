import json
from typing import Dict, List

import numpy as np

from rag.config import VECTOR_PATH


def load_vector_index() -> Dict:
    if not VECTOR_PATH.exists():
        raise FileNotFoundError(
            f"Vector index not found: {VECTOR_PATH}. Run `python -m rag.embeddings` first."
        )

    with VECTOR_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def cosine_similarity(query_vector: List[float], doc_vector: List[float]) -> float:
    q = np.array(query_vector, dtype=np.float32)
    d = np.array(doc_vector, dtype=np.float32)

    q_norm = np.linalg.norm(q)
    d_norm = np.linalg.norm(d)

    if q_norm == 0 or d_norm == 0:
        return 0.0

    return float(np.dot(q, d) / (q_norm * d_norm))


def search_vector_index(
    query_vector: List[float],
    top_k: int = 10,
) -> List[Dict]:
    index_data = load_vector_index()

    scored = []
    for record in index_data["records"]:
        score = cosine_similarity(query_vector, record["embedding"])
        scored.append(
            {
                "chunk_id": record["chunk_id"],
                "document_id": record["document_id"],
                "text": record["text"],
                "metadata": record["metadata"],
                "vector_score": score,
            }
        )

    scored.sort(key=lambda item: item["vector_score"], reverse=True)
    return scored[:top_k]