from typing import Dict, List

from rag.config import TOP_K_RERANKED


def source_priority_boost(metadata: Dict) -> float:
    source_id = (metadata.get("source_id") or "").lower()

    priority = {
        "nci": 0.08,
        "who": 0.07,
        "cdc": 0.07,
        "nhs": 0.06,
        "acs": 0.06,
        "medlineplus": 0.05,
        "ncbi": 0.08,
    }

    return priority.get(source_id, 0.0)


def title_match_boost(query: str, metadata: Dict) -> float:
    query_lower = query.lower()
    title = (metadata.get("title") or "").lower()

    boost = 0.0

    important_terms = [
        "idc",
        "dcis",
        "ilc",
        "breast cancer",
        "symptoms",
        "grading",
        "staging",
        "pathology",
        "biopsy",
        "metastasis",
        "lymph node",
    ]

    for term in important_terms:
        if term in query_lower and term in title:
            boost += 0.03

    return min(boost, 0.12)


def content_match_boost(query: str, text: str) -> float:
    query_lower = query.lower()
    text_lower = text.lower()

    boost = 0.0
    query_terms = [term for term in query_lower.split() if len(term) > 2]

    for term in query_terms:
        if term in text_lower:
            boost += 0.005

    return min(boost, 0.10)


def rerank_results(query: str, results: List[Dict], top_k: int = TOP_K_RERANKED) -> List[Dict]:
    reranked = []

    for item in results:
        metadata = item.get("metadata", {})
        combined_score = float(item.get("combined_score", 0.0))

        final_score = (
            combined_score
            + source_priority_boost(metadata)
            + title_match_boost(query, metadata)
            + content_match_boost(query, item.get("text", ""))
        )

        reranked_item = {
            **item,
            "rerank_score": final_score,
        }
        reranked.append(reranked_item)

    reranked.sort(key=lambda x: x["rerank_score"], reverse=True)
    return reranked[:top_k]