import re
from typing import List, Dict


def clean_text(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = text.replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def split_words(text: str) -> List[str]:
    return text.split()


def join_words(words: List[str]) -> str:
    return " ".join(words).strip()


def chunk_text(
    text: str,
    chunk_size_words: int,
    overlap_words: int,
) -> List[str]:
    words = split_words(clean_text(text))
    if not words:
        return []

    chunks: List[str] = []
    step = max(1, chunk_size_words - overlap_words)

    for start in range(0, len(words), step):
        end = start + chunk_size_words
        chunk_words = words[start:end]
        if not chunk_words:
            continue

        chunk = join_words(chunk_words)
        if chunk:
            chunks.append(chunk)

        if end >= len(words):
            break

    return chunks


def build_chunk_records(
    document_id: str,
    text: str,
    metadata: Dict,
    chunk_size_words: int,
    overlap_words: int,
) -> List[Dict]:
    chunk_texts = chunk_text(
        text=text,
        chunk_size_words=chunk_size_words,
        overlap_words=overlap_words,
    )

    records: List[Dict] = []
    for idx, chunk in enumerate(chunk_texts, start=1):
        chunk_id = f"{document_id}::chunk_{idx:04d}"
        record = {
            "chunk_id": chunk_id,
            "document_id": document_id,
            "text": chunk,
            "metadata": {
                **metadata,
                "chunk_index": idx,
                "total_chunks": len(chunk_texts),
            },
        }
        records.append(record)

    return records