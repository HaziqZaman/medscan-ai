import re
from typing import Dict, List

from rag.config import TOP_K_RETRIEVAL, TOP_K_RERANKED
from rag.embeddings import embed_query
from rag.vector_store import search_vector_index
from rag.bm25_store import search_bm25_index


def tokenize(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z0-9_+-]+", text.lower())


def normalize_scores(items: List[Dict], key: str) -> List[Dict]:
    if not items:
        return items

    values = [item.get(key, 0.0) for item in items]
    min_score = min(values)
    max_score = max(values)

    if max_score == min_score:
        for item in items:
            item[f"{key}_norm"] = 1.0 if max_score > 0 else 0.0
        return items

    for item in items:
        item[f"{key}_norm"] = (
            item.get(key, 0.0) - min_score
        ) / (max_score - min_score)

    return items


def trust_boost(metadata: Dict) -> float:
    if metadata.get("trust_level") == "high":
        return 0.05
    return 0.0


def exact_overlap_boost(query: str, text: str) -> float:
    query_tokens = set(tokenize(query))
    text_tokens = set(tokenize(text))

    if not query_tokens or not text_tokens:
        return 0.0

    overlap = len(query_tokens & text_tokens)
    return min(0.10, overlap * 0.01)


def merge_results(
    query: str,
    vector_results: List[Dict],
    bm25_results: List[Dict],
) -> List[Dict]:
    merged: Dict[str, Dict] = {}

    for item in normalize_scores(vector_results, "vector_score"):
        merged[item["chunk_id"]] = {
            "chunk_id": item["chunk_id"],
            "document_id": item["document_id"],
            "text": item["text"],
            "metadata": item["metadata"],
            "vector_score": item.get("vector_score", 0.0),
            "vector_score_norm": item.get("vector_score_norm", 0.0),
            "bm25_score": 0.0,
            "bm25_score_norm": 0.0,
        }

    for item in normalize_scores(bm25_results, "bm25_score"):
        if item["chunk_id"] not in merged:
            merged[item["chunk_id"]] = {
                "chunk_id": item["chunk_id"],
                "document_id": item["document_id"],
                "text": item["text"],
                "metadata": item["metadata"],
                "vector_score": 0.0,
                "vector_score_norm": 0.0,
                "bm25_score": item.get("bm25_score", 0.0),
                "bm25_score_norm": item.get("bm25_score_norm", 0.0),
            }
        else:
            merged[item["chunk_id"]]["bm25_score"] = item.get("bm25_score", 0.0)
            merged[item["chunk_id"]]["bm25_score_norm"] = item.get("bm25_score_norm", 0.0)

    final_results = []
    for item in merged.values():
        item["combined_score"] = (
            (0.65 * item["vector_score_norm"])
            + (0.35 * item["bm25_score_norm"])
            + trust_boost(item["metadata"])
            + exact_overlap_boost(query, item["text"])
        )
        final_results.append(item)

    final_results.sort(key=lambda x: x["combined_score"], reverse=True)
    return final_results


def hybrid_retrieve(query: str, top_k: int = TOP_K_RERANKED) -> Dict:
    if not query or not query.strip():
        return {
            "scope": "invalid",
            "reason": "empty_query",
            "results": [],
        }

    query_vector = embed_query(query)

    vector_results = search_vector_index(
        query_vector=query_vector,
        top_k=TOP_K_RETRIEVAL,
    )
    bm25_results = search_bm25_index(
        query=query,
        top_k=TOP_K_RETRIEVAL,
    )

    merged_results = merge_results(
        query=query,
        vector_results=vector_results,
        bm25_results=bm25_results,
    )

    return {
        "scope": "retrieval_performed",
        "reason": "hybrid_vector_bm25_search_completed",
        "results": merged_results[:top_k],
    }


def preview_retrieval(query: str, top_k: int = 5) -> None:
    response = hybrid_retrieve(query=query, top_k=top_k)

    print(f"\nScope: {response['scope']}")
    print(f"Reason: {response['reason']}")

    for idx, item in enumerate(response["results"], start=1):
        print("\n" + "=" * 80)
        print(f"Rank: {idx}")
        print(f"Chunk ID: {item['chunk_id']}")
        print(f"Source: {item['metadata'].get('source_label')}")
        print(f"Title: {item['metadata'].get('title')}")
        print(f"Combined Score: {item['combined_score']:.4f}")
        print(f"Vector Score: {item['vector_score']:.4f}")
        print(f"BM25 Score: {item['bm25_score']:.4f}")
        print(f"Text Preview: {item['text'][:400]}...")


if __name__ == "__main__":
    preview_retrieval("What is invasive ductal carcinoma?")