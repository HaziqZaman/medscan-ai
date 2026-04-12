from __future__ import annotations

from collections import deque
from dataclasses import dataclass, asdict
from typing import Dict, Iterable, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse
import time

import requests
from bs4 import BeautifulSoup

from rag.source_registry import (
    SourceDefinition,
    TRUSTED_SOURCES,
    find_source_for_url,
    is_allowed_url_for_source,
    normalize_url,
)

DEFAULT_TIMEOUT = 20
DEFAULT_USER_AGENT = (
    "MedScanAI-RAG-Crawler/1.0 "
    "(educational-use; local-project-testing)"
)


@dataclass
class DiscoveredUrl:
    url: str
    source_id: str
    depth: int
    parent_url: Optional[str] = None
    anchor_text: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


def debug_print(enabled: bool, message: str) -> None:
    if enabled:
        print(message)


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


def is_http_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except Exception:
        return False


def should_skip_href(href: Optional[str]) -> bool:
    if not href:
        return True

    lowered = href.strip().lower()
    return (
        not lowered
        or lowered.startswith("#")
        or lowered.startswith("javascript:")
        or lowered.startswith("mailto:")
        or lowered.startswith("tel:")
        or lowered.startswith("data:")
    )


def make_absolute_url(base_url: str, href: str) -> Optional[str]:
    try:
        absolute = urljoin(base_url, href)
        absolute = normalize_url(absolute)
        if not is_http_url(absolute):
            return None
        return absolute
    except Exception:
        return None


def fetch_html(
    session: requests.Session,
    url: str,
    timeout: int = DEFAULT_TIMEOUT,
    verbose: bool = False,
) -> Optional[str]:
    debug_print(verbose, f"[FETCH] GET {url}")

    try:
        response = session.get(url, timeout=timeout, allow_redirects=True)
        debug_print(verbose, f"[FETCH] STATUS {response.status_code} for {url}")

        response.raise_for_status()

        content_type = (response.headers.get("Content-Type") or "").lower()
        debug_print(verbose, f"[FETCH] CONTENT-TYPE {content_type or 'unknown'}")

        if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
            debug_print(verbose, f"[FETCH] SKIPPED NON-HTML PAGE: {url}")
            return None

        return response.text
    except requests.RequestException as exc:
        debug_print(verbose, f"[FETCH] FAILED {url} | {type(exc).__name__}: {exc}")
        return None


def extract_candidate_links(
    base_url: str,
    html: str,
    verbose: bool = False,
) -> List[Tuple[str, Optional[str]]]:
    soup = BeautifulSoup(html, "html.parser")
    candidates: List[Tuple[str, Optional[str]]] = []

    raw_anchor_count = 0

    for tag in soup.find_all("a", href=True):
        raw_anchor_count += 1
        href = tag.get("href")

        if should_skip_href(href):
            continue

        absolute = make_absolute_url(base_url, href)
        if not absolute:
            continue

        anchor_text = tag.get_text(" ", strip=True) or None
        candidates.append((absolute, anchor_text))

    debug_print(
        verbose,
        f"[LINKS] {base_url} | raw anchors: {raw_anchor_count} | normalized candidates: {len(candidates)}",
    )
    return candidates


def discover_links_from_page(
    page_url: str,
    html: str,
    source: SourceDefinition,
    verbose: bool = False,
) -> List[Tuple[str, Optional[str]]]:
    discovered: List[Tuple[str, Optional[str]]] = []
    seen: Set[str] = set()

    candidates = extract_candidate_links(page_url, html, verbose=verbose)

    allowed_count = 0
    rejected_count = 0

    for absolute_url, anchor_text in candidates:
        if absolute_url in seen:
            continue

        if not is_allowed_url_for_source(absolute_url, source):
            rejected_count += 1
            continue

        seen.add(absolute_url)
        allowed_count += 1
        discovered.append((absolute_url, anchor_text))

    debug_print(
        verbose,
        f"[FILTER] {page_url} | allowed: {allowed_count} | rejected: {rejected_count}",
    )

    if verbose and discovered[:10]:
        for idx, (url, _) in enumerate(discovered[:10], start=1):
            print(f"         -> allowed {idx:02d}: {url}")

        if len(discovered) > 10:
            print(f"         -> ... {len(discovered) - 10} more allowed links")

    return discovered


def resolve_source_for_seed(
    seed_url: str,
    explicit_source_id: Optional[str] = None,
) -> Optional[SourceDefinition]:
    if explicit_source_id:
        return TRUSTED_SOURCES.get(explicit_source_id)

    return find_source_for_url(seed_url)


def discover_source_urls(
    seed_url: str,
    source_id: Optional[str] = None,
    max_pages: Optional[int] = None,
    max_depth: Optional[int] = None,
    timeout: int = DEFAULT_TIMEOUT,
    sleep_seconds: float = 0.25,
    session: Optional[requests.Session] = None,
    verbose: bool = False,
) -> List[DiscoveredUrl]:
    source = resolve_source_for_seed(seed_url, explicit_source_id=source_id)
    if not source:
        debug_print(verbose, f"[SOURCE] No source matched for seed: {seed_url}")
        return []

    seed_url = normalize_url(seed_url)

    if not is_allowed_url_for_source(seed_url, source):
        debug_print(verbose, f"[SOURCE] Seed URL rejected by source rules: {seed_url}")
        return []

    effective_max_pages = max_pages if max_pages is not None else source.max_pages
    effective_max_depth = max_depth if max_depth is not None else source.crawl_depth

    debug_print(verbose, "\n" + "=" * 100)
    debug_print(verbose, f"[SOURCE] {source.source_id} | {source.label}")
    debug_print(verbose, f"[SEED]   {seed_url}")
    debug_print(verbose, f"[LIMITS] max_pages={effective_max_pages} | max_depth={effective_max_depth}")
    debug_print(verbose, "=" * 100)

    own_session = session is None
    session = session or build_session()

    queue = deque([(seed_url, 0, None, None)])
    visited: Set[str] = set()
    results: List[DiscoveredUrl] = []

    try:
        while queue and len(results) < effective_max_pages:
            current_url, depth, parent_url, anchor_text = queue.popleft()

            if current_url in visited:
                continue
            visited.add(current_url)

            debug_print(verbose, f"\n[VISIT] depth={depth} | {current_url}")

            results.append(
                DiscoveredUrl(
                    url=current_url,
                    source_id=source.source_id,
                    depth=depth,
                    parent_url=parent_url,
                    anchor_text=anchor_text,
                )
            )

            if depth >= effective_max_depth:
                debug_print(verbose, f"[VISIT] depth limit reached for {current_url}")
                continue

            html = fetch_html(
                session=session,
                url=current_url,
                timeout=timeout,
                verbose=verbose,
            )
            if not html:
                debug_print(verbose, f"[VISIT] no HTML extracted from {current_url}")
                continue

            child_links = discover_links_from_page(
                page_url=current_url,
                html=html,
                source=source,
                verbose=verbose,
            )

            enqueued_now = 0
            for child_url, child_anchor_text in child_links:
                if child_url in visited:
                    continue
                queue.append((child_url, depth + 1, current_url, child_anchor_text))
                enqueued_now += 1

            debug_print(verbose, f"[QUEUE] added {enqueued_now} child URLs from {current_url}")
            debug_print(verbose, f"[QUEUE] current queue size: {len(queue)}")

            if sleep_seconds > 0:
                time.sleep(sleep_seconds)

        debug_print(verbose, f"\n[RESULT] total discovered for {source.source_id}: {len(results)}")
    finally:
        if own_session:
            session.close()

    return results


def discover_all_sources(
    source_id: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT,
    sleep_seconds: float = 0.25,
    verbose: bool = False,
) -> Dict[str, List[DiscoveredUrl]]:
    session = build_session()
    output: Dict[str, List[DiscoveredUrl]] = {}

    try:
        target_sources: Iterable[str]
        if source_id:
            target_sources = [source_id]
        else:
            target_sources = TRUSTED_SOURCES.keys()

        for current_source_id in target_sources:
            source = TRUSTED_SOURCES.get(current_source_id)
            if not source:
                continue

            debug_print(verbose, "\n" + "#" * 100)
            debug_print(verbose, f"[DISCOVERY] START SOURCE {current_source_id} | seeds={len(source.seed_urls)}")
            debug_print(verbose, "#" * 100)

            merged: Dict[str, DiscoveredUrl] = {}

            for seed_url in source.seed_urls:
                results = discover_source_urls(
                    seed_url=seed_url,
                    source_id=current_source_id,
                    timeout=timeout,
                    sleep_seconds=sleep_seconds,
                    session=session,
                    verbose=verbose,
                )

                for item in results:
                    if item.url not in merged:
                        merged[item.url] = item

            ordered = sorted(
                merged.values(),
                key=lambda item: (item.depth, item.url),
            )
            output[current_source_id] = ordered

            debug_print(
                verbose,
                f"[DISCOVERY] END SOURCE {current_source_id} | unique discovered={len(ordered)}",
            )
    finally:
        session.close()

    return output


def flatten_discovery_map(discovery_map: Dict[str, List[DiscoveredUrl]]) -> List[dict]:
    rows: List[dict] = []
    for source_id, items in discovery_map.items():
        for item in items:
            row = item.to_dict()
            row["source_id"] = source_id
            rows.append(row)
    return rows


def preview_discovery(source_id: Optional[str] = None, verbose: bool = True) -> None:
    discovery_map = discover_all_sources(
        source_id=source_id,
        verbose=verbose,
    )

    print("\n" + "=" * 100)
    print("FINAL DISCOVERY SUMMARY")
    print("=" * 100)

    total_urls = 0
    for current_source_id, items in discovery_map.items():
        total_urls += len(items)
        print(f"{current_source_id}: {len(items)} URLs")

        for idx, item in enumerate(items[:10], start=1):
            print(f"  {idx:02d}. depth={item.depth} | {item.url}")

        if len(items) > 10:
            print(f"  ... {len(items) - 10} more")

    print("-" * 100)
    print(f"TOTAL URLS DISCOVERED: {total_urls}")


if __name__ == "__main__":
    preview_discovery(verbose=True)