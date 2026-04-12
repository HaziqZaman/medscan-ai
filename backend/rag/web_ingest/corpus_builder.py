from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Set

from rag.web_ingest.url_discovery import discover_all_sources, flatten_discovery_map
from rag.web_ingest.extractor import extract_many_urls, ExtractedDocument

OUTPUT_DIR = Path("storage/docs/medical_sources")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def slugify(value: str) -> str:
    value = value.lower().strip()
    cleaned = []
    for ch in value:
        if ch.isalnum():
            cleaned.append(ch)
        elif ch in {" ", "-", "_"}:
            cleaned.append("_")
    result = "".join(cleaned)
    while "__" in result:
        result = result.replace("__", "_")
    return result.strip("_") or "document"


def build_output_filename(doc: ExtractedDocument, index: int) -> str:
    source_id = doc.metadata.get("source_id", "unknown")
    title_slug = slugify(doc.title)[:80]
    return f"{source_id}_{index:03d}_{title_slug}.json"


def build_serializable_document(doc: ExtractedDocument) -> Dict:
    return {
        "document_id": doc.content_hash[:16],
        "title": doc.title,
        "url": doc.url,
        "content": doc.text,
        "content_hash": doc.content_hash,
        "word_count": doc.word_count,
        "char_count": doc.char_count,
        "extracted_at": doc.extracted_at,
        "metadata": doc.metadata,
    }


def save_document(doc: ExtractedDocument, index: int, output_dir: Path = OUTPUT_DIR) -> Path:
    filename = build_output_filename(doc, index)
    output_path = output_dir / filename

    payload = build_serializable_document(doc)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return output_path


def clear_existing_json_docs(output_dir: Path = OUTPUT_DIR) -> int:
    removed = 0
    for file_path in output_dir.glob("*.json"):
        file_path.unlink(missing_ok=True)
        removed += 1
    return removed


def build_corpus(
    source_id: Optional[str] = None,
    clear_existing: bool = False,
) -> Dict:
    if clear_existing:
        removed = clear_existing_json_docs()
        print(f"[CLEANUP] Removed {removed} old JSON documents.")
    else:
        removed = 0

    discovery_map = discover_all_sources(source_id=source_id, verbose=False)
    discovered_rows = flatten_discovery_map(discovery_map)
    urls = [row["url"] for row in discovered_rows]

    print(f"[DISCOVERY] Total discovered URLs: {len(urls)}")

    extracted_docs = extract_many_urls(urls)
    print(f"[EXTRACTION] Extracted acceptable documents: {len(extracted_docs)}")

    saved_paths: List[str] = []
    seen_hashes: Set[str] = set()
    duplicate_count = 0

    for idx, doc in enumerate(extracted_docs, start=1):
        if doc.content_hash in seen_hashes:
            duplicate_count += 1
            continue

        seen_hashes.add(doc.content_hash)
        path = save_document(doc, index=len(saved_paths) + 1)
        saved_paths.append(str(path))

    summary = {
        "source_id": source_id or "all",
        "removed_old_docs": removed,
        "discovered_url_count": len(urls),
        "extracted_doc_count": len(extracted_docs),
        "saved_doc_count": len(saved_paths),
        "duplicate_count": duplicate_count,
        "output_dir": str(OUTPUT_DIR),
        "saved_files": saved_paths,
    }

    print("\n" + "=" * 100)
    print("CORPUS BUILD SUMMARY")
    print("=" * 100)
    print(f"Discovered URLs:   {summary['discovered_url_count']}")
    print(f"Extracted docs:    {summary['extracted_doc_count']}")
    print(f"Duplicates skipped:{summary['duplicate_count']}")
    print(f"Saved docs:        {summary['saved_doc_count']}")
    print(f"Output dir:        {summary['output_dir']}")

    return summary


def preview_saved_docs(limit: int = 10, output_dir: Path = OUTPUT_DIR) -> None:
    files = sorted(output_dir.glob("*.json"))
    print(f"\nSaved JSON docs: {len(files)}")

    for idx, file_path in enumerate(files[:limit], start=1):
        print(f"{idx:02d}. {file_path.name}")

    if len(files) > limit:
        print(f"... {len(files) - limit} more")


if __name__ == "__main__":
    build_corpus(clear_existing=True)
    preview_saved_docs()