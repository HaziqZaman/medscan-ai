import json
import math
import re
from collections import Counter
from typing import Dict, List

from rag.config import BM25_PATH, CHUNKS_PATH


BM25_K1 = 1.5
BM25_B = 0.75


def tokenize(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z0-9_+-]+", text.lower())


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


def build_bm25_index() -> Dict:
    records = load_chunk_records()
    total_docs = len(records)

    documents = []
    document_frequency: Counter = Counter()
    total_length = 0

    for record in records:
        tokens = tokenize(record["text"])
        term_freqs = Counter(tokens)
        total_length += len(tokens)

        for term in term_freqs.keys():
            document_frequency[term] += 1

        documents.append(
            {
                "chunk_id": record["chunk_id"],
                "document_id": record["document_id"],
                "text": record["text"],
                "metadata": record["metadata"],
                "tokens": tokens,
                "term_freqs": dict(term_freqs),
                "length": len(tokens),
            }
        )

    avg_doc_len = (total_length / total_docs) if total_docs else 0.0

    idf = {}
    for term, df in document_frequency.items():
        idf[term] = math.log(1 + ((total_docs - df + 0.5) / (df + 0.5)))

    return {
        "total_docs": total_docs,
        "avg_doc_len": avg_doc_len,
        "idf": idf,
        "documents": documents,
    }


def save_bm25_index(index_data: Dict) -> None:
    with BM25_PATH.open("w", encoding="utf-8") as f:
        json.dump(index_data, f, ensure_ascii=False)


def load_bm25_index() -> Dict:
    if not BM25_PATH.exists():
        raise FileNotFoundError(
            f"BM25 index not found: {BM25_PATH}. Run `python -m rag.bm25_store` first."
        )

    with BM25_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def score_document(query_tokens: List[str], document: Dict, idf: Dict, avg_doc_len: float) -> float:
    score = 0.0
    doc_len = max(1, document["length"])
    term_freqs = document["term_freqs"]

    for token in query_tokens:
        tf = term_freqs.get(token, 0)
        if tf == 0:
            continue

        token_idf = idf.get(token, 0.0)
        numerator = tf * (BM25_K1 + 1)
        denominator = tf + BM25_K1 * (1 - BM25_B + BM25_B * (doc_len / max(avg_doc_len, 1.0)))
        score += token_idf * (numerator / denominator)

    return score


def search_bm25_index(query: str, top_k: int = 10) -> List[Dict]:
    index_data = load_bm25_index()
    query_tokens = tokenize(query)

    if not query_tokens:
        return []

    scored = []
    for document in index_data["documents"]:
        score = score_document(
            query_tokens=query_tokens,
            document=document,
            idf=index_data["idf"],
            avg_doc_len=index_data["avg_doc_len"],
        )
        scored.append(
            {
                "chunk_id": document["chunk_id"],
                "document_id": document["document_id"],
                "text": document["text"],
                "metadata": document["metadata"],
                "bm25_score": score,
            }
        )

    scored.sort(key=lambda item: item["bm25_score"], reverse=True)
    return scored[:top_k]


def main() -> None:
    print("Building BM25 index from chunk records...")
    index_data = build_bm25_index()
    save_bm25_index(index_data)

    print("BM25 index complete.")
    print(f"Saved to: {BM25_PATH}")
    print(f"Total documents: {index_data['total_docs']}")
    print(f"Average document length: {index_data['avg_doc_len']:.2f}")


if __name__ == "__main__":
    main()