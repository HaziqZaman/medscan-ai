from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from hashlib import sha256
from typing import Dict, List, Optional
from urllib.parse import urlparse
import re

import requests
import trafilatura
from bs4 import BeautifulSoup

from rag.source_registry import build_url_document_metadata, normalize_url


DEFAULT_TIMEOUT = 25
DEFAULT_USER_AGENT = (
    "MedScanAI-RAG-Extractor/1.0 "
    "(educational-use; local-project-testing)"
)

MIN_WORD_COUNT = 50

TOPIC_SIGNALS = [
    "breast",
    "cancer",
    "carcinoma",
    "tumor",
    "tumour",
    "oncology",
    "biopsy",
    "mammogram",
    "metast",
    "lymph",
    "her2",
    "histopathology",
    "pathology",
    "ductal",
    "lobular",
    "idc",
    "dcis",
    "ilc",
    "chemotherapy",
    "radiotherapy",
    "hormone",
    "staging",
    "grading",
]

NOISE_PATTERNS = [
    "javascript is disabled",
    "cookie policy",
    "accept cookies",
    "all rights reserved",
    "skip to main content",
]


@dataclass
class ExtractedDocument:
    url: str
    title: str
    text: str
    metadata: Dict
    word_count: int
    char_count: int
    content_hash: str
    extracted_at: str

    def to_dict(self) -> dict:
        return asdict(self)


def build_session(user_agent: str = DEFAULT_USER_AGENT) -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        }
    )
    return session


def normalize_whitespace(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"\r\n|\r", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def get_html(
    session: requests.Session,
    url: str,
    timeout: int = DEFAULT_TIMEOUT,
) -> Optional[str]:
    try:
        response = session.get(url, timeout=timeout, allow_redirects=True)
        response.raise_for_status()

        content_type = (response.headers.get("Content-Type") or "").lower()
        if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
            return None

        return response.text
    except requests.RequestException:
        return None


def extract_title_from_html(html: str, url: str) -> str:
    try:
        soup = BeautifulSoup(html, "html.parser")
        title_tag = soup.find("title")
        if title_tag and title_tag.get_text(strip=True):
            return title_tag.get_text(" ", strip=True)
    except Exception:
        pass

    parsed = urlparse(url)
    fallback = parsed.path.rstrip("/").split("/")[-1].replace("-", " ").replace("_", " ").strip()
    return fallback or parsed.netloc


def extract_main_text(html: str, url: str) -> str:
    extracted = trafilatura.extract(
        html,
        url=url,
        favor_precision=True,
        include_comments=False,
        include_tables=True,
        no_fallback=False,
    )

    if not extracted:
        return ""

    return normalize_whitespace(extracted)


def count_words(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def contains_topic_signal(url: str, text: str) -> bool:
    combined = f"{url}\n{text}".lower()
    return any(signal in combined for signal in TOPIC_SIGNALS)


def is_noisy_text(text: str) -> bool:
    lowered = text.lower()
    return any(pattern in lowered for pattern in NOISE_PATTERNS)


def build_content_hash(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def extract_url_to_document(
    url: str,
    session: Optional[requests.Session] = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> Optional[ExtractedDocument]:
    normalized_url = normalize_url(url)
    print(f"\n[START] {normalized_url}")

    own_session = session is None
    session = session or build_session()

    try:
        html = get_html(session=session, url=normalized_url, timeout=timeout)
        if not html:
            print("[FAIL] get_html returned None")
            return None
        print(f"[OK] HTML fetched | length={len(html)}")

        title = extract_title_from_html(html, normalized_url)
        print(f"[OK] Title extracted: {title}")

        text = extract_main_text(html, normalized_url)
        if not text:
            print("[FAIL] extract_main_text returned empty text")
            return None
        print(f"[OK] Main text extracted | chars={len(text)}")

        word_count = count_words(text)
        print(f"[INFO] Word count = {word_count}")
        if word_count < MIN_WORD_COUNT:
            print(f"[FAIL] Word count below MIN_WORD_COUNT ({MIN_WORD_COUNT})")
            return None

        noisy = is_noisy_text(text)
        print(f"[INFO] is_noisy_text = {noisy}")
        if noisy:
            print("[FAIL] Text rejected as noisy")
            return None

        topic_ok = contains_topic_signal(normalized_url, text)
        print(f"[INFO] contains_topic_signal = {topic_ok}")
        if not topic_ok:
            print("[FAIL] No topic signal matched")
            return None

        metadata = build_url_document_metadata(
            url=normalized_url,
            title=title,
            extra={
                "ingest_type": "web_page",
                "word_count": word_count,
            },
        )

        print("[SUCCESS] Document accepted")

        return ExtractedDocument(
            url=normalized_url,
            title=title,
            text=text,
            metadata=metadata,
            word_count=word_count,
            char_count=len(text),
            content_hash=build_content_hash(text),
            extracted_at=datetime.now(timezone.utc).isoformat(),
        )
    finally:
        if own_session:
            session.close()

def extract_many_urls(
    urls: List[str],
    timeout: int = DEFAULT_TIMEOUT,
) -> List[ExtractedDocument]:
    session = build_session()
    documents: List[ExtractedDocument] = []

    try:
        for url in urls:
            doc = extract_url_to_document(
                url=url,
                session=session,
                timeout=timeout,
            )
            if doc is not None:
                documents.append(doc)
    finally:
        session.close()

    return documents


def preview_extraction(url: str) -> None:
    doc = extract_url_to_document(url)
    if not doc:
        print("\nNo extractable document returned.")
        return

    print("\n" + "=" * 100)
    print("EXTRACTED DOCUMENT")
    print("=" * 100)
    print(f"URL: {doc.url}")
    print(f"TITLE: {doc.title}")
    print(f"WORDS: {doc.word_count}")
    print(f"CHARS: {doc.char_count}")
    print(f"HASH: {doc.content_hash}")
    print("-" * 100)
    print(doc.text[:2000])
    if len(doc.text) > 2000:
        print("\n... truncated ...")

if __name__ == "__main__":
    preview_extraction("https://www.nhs.uk/conditions/breast-cancer")