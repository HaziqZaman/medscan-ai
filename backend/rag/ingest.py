import json
from pathlib import Path
from typing import Dict, List, Optional

from rag.config import (
    DOCS_DIR,
    CHUNKS_PATH,
    MANIFEST_PATH,
    ALLOWED_EXTENSIONS,
    CHUNK_SIZE_WORDS,
    CHUNK_OVERLAP_WORDS,
    ensure_directories,
)
from rag.chunker import clean_text, build_chunk_records
from rag.source_registry import metadata_with_document_fields, as_serializable_registry


# New web-ingested corpus location
WEB_DOCS_DIR = Path("storage/docs/medical_sources")


def read_text_file(file_path: Path) -> str:
    return file_path.read_text(encoding="utf-8", errors="ignore")


def read_markdown_file(file_path: Path) -> str:
    return file_path.read_text(encoding="utf-8", errors="ignore")


def read_html_file(file_path: Path) -> str:
    raw = file_path.read_text(encoding="utf-8", errors="ignore")
    raw = raw.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    import re
    text = re.sub(r"<[^>]+>", " ", raw)
    return text


def read_pdf_file(file_path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError(
            "PDF support requires pypdf. Install it with: pip install pypdf"
        ) from exc

    reader = PdfReader(str(file_path))
    pages = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        if page_text.strip():
            pages.append(page_text)
    return "\n\n".join(pages)


def read_document(file_path: Path) -> str:
    suffix = file_path.suffix.lower()

    if suffix == ".txt":
        return read_text_file(file_path)
    if suffix == ".md":
        return read_markdown_file(file_path)
    if suffix in {".html", ".htm"}:
        return read_html_file(file_path)
    if suffix == ".pdf":
        return read_pdf_file(file_path)

    raise ValueError(f"Unsupported file type: {file_path.suffix}")


def list_supported_documents() -> List[Path]:
    return sorted(
        [
            path
            for path in DOCS_DIR.rglob("*")
            if path.is_file() and path.suffix.lower() in ALLOWED_EXTENSIONS
        ]
    )


def list_web_json_documents() -> List[Path]:
    if not WEB_DOCS_DIR.exists():
        return []

    return sorted(
        [
            path
            for path in WEB_DOCS_DIR.glob("*.json")
            if path.is_file()
        ]
    )


def read_web_json_document(file_path: Path) -> Optional[Dict]:
    try:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"Skipped invalid JSON document {file_path.name}: {exc}")
        return None

    text = payload.get("content") or payload.get("text") or ""
    text = clean_text(text)

    if not text:
        print(f"Skipped empty JSON document: {file_path.name}")
        return None

    metadata = payload.get("metadata") or {}
    if not isinstance(metadata, dict):
        metadata = {}

    metadata.update(
        {
            "document_path": str(file_path),
            "filename": file_path.name,
            "title": payload.get("title") or metadata.get("title") or file_path.stem,
            "url": payload.get("url") or metadata.get("url"),
            "content_hash": payload.get("content_hash"),
            "word_count": payload.get("word_count"),
            "char_count": payload.get("char_count"),
            "extracted_at": payload.get("extracted_at"),
            "ingest_source": "web_json_corpus",
        }
    )

    document_id = payload.get("document_id") or file_path.stem

    return {
        "document_id": document_id,
        "filename": file_path.name,
        "text": text,
        "metadata": metadata,
    }


def build_document_manifest(documents: List[Dict]) -> Dict:
    return {
        "total_documents": len(documents),
        "documents": documents,
        "trusted_registry": as_serializable_registry(),
    }


def ingest_web_json_corpus(files: List[Path]) -> None:
    all_chunk_records: List[Dict] = []
    manifest_docs: List[Dict] = []

    print(f"Using web JSON corpus from: {WEB_DOCS_DIR}")
    print(f"Total JSON documents found: {len(files)}")

    for file_path in files:
        print(f"Processing JSON: {file_path.name}")

        parsed = read_web_json_document(file_path)
        if not parsed:
            continue

        chunk_records = build_chunk_records(
            document_id=parsed["document_id"],
            text=parsed["text"],
            metadata=parsed["metadata"],
            chunk_size_words=CHUNK_SIZE_WORDS,
            overlap_words=CHUNK_OVERLAP_WORDS,
        )

        all_chunk_records.extend(chunk_records)
        manifest_docs.append(
            {
                "document_id": parsed["document_id"],
                "filename": parsed["filename"],
                "chunks": len(chunk_records),
                "metadata": parsed["metadata"],
            }
        )

        print(f" -> chunks created: {len(chunk_records)}")

    with CHUNKS_PATH.open("w", encoding="utf-8") as f:
        for record in all_chunk_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    with MANIFEST_PATH.open("w", encoding="utf-8") as f:
        json.dump(build_document_manifest(manifest_docs), f, ensure_ascii=False, indent=2)

    print("\nIngestion complete.")
    print(f"Chunks saved to: {CHUNKS_PATH}")
    print(f"Manifest saved to: {MANIFEST_PATH}")
    print(f"Total chunks: {len(all_chunk_records)}")


def ingest_legacy_corpus(files: List[Path]) -> None:
    all_chunk_records: List[Dict] = []
    manifest_docs: List[Dict] = []

    print(f"Using legacy document corpus from: {DOCS_DIR}")
    print(f"Total supported legacy files found: {len(files)}")

    for file_path in files:
        print(f"Processing: {file_path.name}")

        text = clean_text(read_document(file_path))
        if not text:
            print(f"Skipped empty document: {file_path.name}")
            continue

        document_id = file_path.stem
        metadata = metadata_with_document_fields(
            file_path=file_path,
            extra={
                "document_path": str(file_path),
                "ingest_source": "legacy_file_corpus",
            },
        )

        chunk_records = build_chunk_records(
            document_id=document_id,
            text=text,
            metadata=metadata,
            chunk_size_words=CHUNK_SIZE_WORDS,
            overlap_words=CHUNK_OVERLAP_WORDS,
        )

        all_chunk_records.extend(chunk_records)
        manifest_docs.append(
            {
                "document_id": document_id,
                "filename": file_path.name,
                "chunks": len(chunk_records),
                "metadata": metadata,
            }
        )

        print(f" -> chunks created: {len(chunk_records)}")

    with CHUNKS_PATH.open("w", encoding="utf-8") as f:
        for record in all_chunk_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    with MANIFEST_PATH.open("w", encoding="utf-8") as f:
        json.dump(build_document_manifest(manifest_docs), f, ensure_ascii=False, indent=2)

    print("\nIngestion complete.")
    print(f"Chunks saved to: {CHUNKS_PATH}")
    print(f"Manifest saved to: {MANIFEST_PATH}")
    print(f"Total chunks: {len(all_chunk_records)}")


def main() -> None:
    ensure_directories()

    web_json_files = list_web_json_documents()
    if web_json_files:
        ingest_web_json_corpus(web_json_files)
        return

    legacy_files = list_supported_documents()
    if legacy_files:
        ingest_legacy_corpus(legacy_files)
        return

    print(f"No supported legacy files found in: {DOCS_DIR}")
    print(f"No web JSON corpus files found in: {WEB_DOCS_DIR}")


if __name__ == "__main__":
    main()