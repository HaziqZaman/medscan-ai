from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Dict, Optional, List
from urllib.parse import urlparse, urlunparse
import re


BINARY_EXTENSIONS = {
    ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp",
    ".zip", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".mp4", ".mp3", ".avi", ".mov", ".wmv", ".csv", ".xml", ".json",
}

GLOBAL_BLOCKED_URL_KEYWORDS = [
    "/es/",
    "/espanol/",
    "/spanish/",
    "/podcasts/",
    "/podcast/",
    "/news/item/",
    "/news-events/",
    "/newsroom/",
    "/media/",
    "/site.html",
    "/advisory-committee/",
    "/contact",
    "/donate",
    "/about-us",
    "/social-media",
    "/socialmedia",
    "/videos",
    "/video/",
    "/audio/",
    "/press-release",
    "/press-releases",
    "/newsletter",
    "/events",
    "/event/",
]

GLOBAL_TOPIC_MUST_HAVE = [
    "breast",
    "carcinoma",
    "mammogram",
    "histopathology",
    "biopsy",
    "metast",
    "lymph",
    "her2",
    "hormone",
    "idc",
    "dcis",
    "ilc",
    "oncology",
    "tumor",
    "tumour",
]

GLOBAL_BLOCKED_TOPIC_DRIFT = [
    "breastfeeding",
    "breast reconstruction",
    "breastreconstruction",
    "cosmetic",
    "implant surgery",
    "plastic surgery",
]


@dataclass
class SourceDefinition:
    source_id: str
    label: str
    domain: str
    allowed_domains: List[str]
    trust_level: str
    audience: str
    default_topic: str
    language: str
    seed_urls: List[str] = field(default_factory=list)
    allowed_path_prefixes: List[str] = field(default_factory=list)
    include_url_keywords: List[str] = field(default_factory=list)
    blocked_path_keywords: List[str] = field(default_factory=list)
    blocked_exact_paths: List[str] = field(default_factory=list)
    max_pages: int = 40
    crawl_depth: int = 2


TRUSTED_SOURCES: Dict[str, SourceDefinition] = {
    "nci": SourceDefinition(
        source_id="nci",
        label="National Cancer Institute",
        domain="cancer.gov",
        allowed_domains=["cancer.gov", "www.cancer.gov"],
        trust_level="high",
        audience="student_and_professional",
        default_topic="breast_cancer",
        language="en",
        seed_urls=[
            "https://www.cancer.gov/types/breast",
            "https://www.cancer.gov/types/breast/breast-changes",
            "https://www.cancer.gov/types/breast/breast-hormone-therapy-fact-sheet",
        ],
        allowed_path_prefixes=[
            "/types/breast",
            "/about-cancer/treatment/drugs",
            "/publications/dictionaries/cancer-terms",
        ],
        include_url_keywords=[
            "breast",
            "carcinoma",
            "biopsy",
            "stage",
            "staging",
            "treatment",
            "metastatic",
            "metastasis",
            "hormone",
            "her2",
            "lymph",
            "ductal",
            "lobular",
        ],
        blocked_path_keywords=[
            "search",
            "research",
            "grants-training",
            "about-nci",
            "espanol",
            "news",
            "podcast",
            "childhood",
        ],
        blocked_exact_paths=[],
        max_pages=40,
        crawl_depth=2,
    ),
    "who": SourceDefinition(
        source_id="who",
        label="World Health Organization",
        domain="who.int",
        allowed_domains=["who.int", "www.who.int"],
        trust_level="high",
        audience="general_and_student",
        default_topic="breast_cancer",
        language="en",
        seed_urls=[
            "https://www.who.int/news-room/fact-sheets/detail/breast-cancer",
        ],
        allowed_path_prefixes=[
            "/news-room/fact-sheets/detail",
            "/health-topics/cancer",
            "/initiatives/global-breast-cancer-initiative",
        ],
        include_url_keywords=[
            "breast-cancer",
            "breast",
            "cancer",
            "oncology",
        ],
        blocked_path_keywords=[
            "podcast",
            "news/item",
            "publications",
            "countries",
            "emergencies",
            "data",
            "audio",
            "video",
        ],
        blocked_exact_paths=[
            "/news-room/fact-sheets",
            "/news-room/fact-sheets/detail",
        ],
        max_pages=12,
        crawl_depth=1,
    ),
    "cdc": SourceDefinition(
        source_id="cdc",
        label="Centers for Disease Control and Prevention",
        domain="cdc.gov",
        allowed_domains=["cdc.gov", "www.cdc.gov"],
        trust_level="high",
        audience="general_and_student",
        default_topic="breast_cancer",
        language="en",
        seed_urls=[
            "https://www.cdc.gov/breast-cancer",
        ],
        allowed_path_prefixes=[
            "/breast-cancer",
            "/cancer/breast",
        ],
        include_url_keywords=[
            "breast-cancer",
            "breast",
            "screening",
            "symptoms",
            "risk",
            "mammogram",
        ],
        blocked_path_keywords=[
            "es",
            "advisory-committee",
            "site",
            "media",
            "contact",
            "podcast",
            "news",
        ],
        blocked_exact_paths=[],
        max_pages=18,
        crawl_depth=2,
    ),
    "nhs": SourceDefinition(
        source_id="nhs",
        label="NHS",
        domain="nhs.uk",
        allowed_domains=["nhs.uk", "www.nhs.uk"],
        trust_level="high",
        audience="general_and_student",
        default_topic="breast_cancer",
        language="en",
        seed_urls=[
            "https://www.nhs.uk/conditions/breast-cancer",
        ],
        allowed_path_prefixes=[
            "/conditions/breast-cancer",
            "/conditions/breast-cancer-in-women",
            "/conditions/breast-cancer-in-men",
        ],
        include_url_keywords=[
            "breast-cancer",
            "breast",
            "cancer",
            "symptoms",
            "treatment",
            "tests",
            "causes",
        ],
        blocked_path_keywords=[
            "live-well",
            "mental-health",
            "services-near-you",
            "medicines",
            "pregnancy",
            "baby",
        ],
        blocked_exact_paths=[],
        max_pages=20,
        crawl_depth=2,
    ),
    "acs": SourceDefinition(
        source_id="acs",
        label="American Cancer Society",
        domain="cancer.org",
        allowed_domains=["cancer.org", "www.cancer.org"],
        trust_level="high",
        audience="general_and_student",
        default_topic="breast_cancer",
        language="en",
        seed_urls=[
            "https://www.cancer.org/cancer/types/breast-cancer.html",
        ],
        allowed_path_prefixes=[
            "/cancer/types/breast-cancer",
            "/cancer/diagnosis-staging/tests/pathology-reports",
            "/treatment",
        ],
        include_url_keywords=[
            "breast-cancer",
            "breast",
            "stage",
            "staging",
            "biopsy",
            "pathology",
            "her2",
            "hormone",
            "metastatic",
            "lobular",
            "ductal",
        ],
        blocked_path_keywords=[
            "donate",
            "involved",
            "about-us",
            "research",
            "side-effects/hair",
            "care-toolkit",
            "news",
            "podcast",
        ],
        blocked_exact_paths=[],
        max_pages=30,
        crawl_depth=2,
    ),
    "medlineplus": SourceDefinition(
        source_id="medlineplus",
        label="MedlinePlus",
        domain="medlineplus.gov",
        allowed_domains=["medlineplus.gov", "www.medlineplus.gov"],
        trust_level="high",
        audience="general_and_student",
        default_topic="breast_cancer",
        language="en",
        seed_urls=[
            "https://medlineplus.gov/breastcancer.html",
        ],
        allowed_path_prefixes=[
            "/breastcancer.html",
            "/cancer.html",
            "/cancerchemotherapy.html",
            "/ency/article",
        ],
        include_url_keywords=[
            "breastcancer",
            "breast-cancer",
            "breast",
            "cancer",
            "metastatic",
            "stage",
            "treatment",
            "biopsy",
            "mammogram",
        ],
        blocked_path_keywords=[
            "breastfeeding",
            "breastreconstruction",
            "genetics",
            "lab",
            "druginfo",
            "video",
            "spanish",
        ],
        blocked_exact_paths=[],
        max_pages=18,
        crawl_depth=2,
    ),
    "ncbi": SourceDefinition(
        source_id="ncbi",
        label="NCBI Bookshelf / PubMed Books",
        domain="ncbi.nlm.nih.gov",
        allowed_domains=["ncbi.nlm.nih.gov", "www.ncbi.nlm.nih.gov"],
        trust_level="high",
        audience="student_and_professional",
        default_topic="breast_cancer",
        language="en",
        seed_urls=[
            "https://www.ncbi.nlm.nih.gov/books/NBK430685",
            "https://www.ncbi.nlm.nih.gov/books/NBK459145",
        ],
        allowed_path_prefixes=[
            "/books/NBK",
        ],
        include_url_keywords=[
            "breast",
            "cancer",
            "carcinoma",
            "staging",
            "treatment",
            "pathology",
            "histopathology",
            "metastasis",
        ],
        blocked_path_keywords=[
            "pubmed",
            "gene",
            "taxonomy",
            "protein",
            "sra",
            "nuccore",
            "bookshelf_br.fcgi",
        ],
        blocked_exact_paths=[
            "/books",
        ],
        max_pages=20,
        crawl_depth=1,
    ),
}


def normalize_domain(domain: str) -> str:
    domain = domain.strip().lower()
    if domain.startswith("www."):
        return domain[4:]
    return domain


def normalize_url(url: str) -> str:
    parsed = urlparse(url.strip())
    scheme = parsed.scheme.lower() or "https"
    netloc = parsed.netloc.lower()
    path = parsed.path or "/"

    normalized = parsed._replace(
        scheme=scheme,
        netloc=netloc,
        fragment="",
        query="",
        params="",
        path=path.rstrip("/") if path != "/" else "/",
    )
    return urlunparse(normalized)


def detect_source_id_from_filename(file_path: Path) -> Optional[str]:
    name = file_path.stem.lower()
    prefix = name.split("_")[0]
    if prefix in TRUSTED_SOURCES:
        return prefix
    return None


def get_source_by_id(source_id: str) -> Optional[SourceDefinition]:
    return TRUSTED_SOURCES.get(source_id)


def find_source_for_domain(domain: str) -> Optional[SourceDefinition]:
    domain = normalize_domain(domain)

    for source in TRUSTED_SOURCES.values():
        allowed = {normalize_domain(d) for d in source.allowed_domains}
        if domain in allowed:
            return source

    return None


def find_source_for_url(url: str) -> Optional[SourceDefinition]:
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
    except Exception:
        return None

    return find_source_for_domain(domain)


def has_blocked_extension(url: str) -> bool:
    path = urlparse(url).path.lower()
    return any(path.endswith(ext) for ext in BINARY_EXTENSIONS)


def clean_path(path: str) -> str:
    if not path:
        return "/"
    if not path.startswith("/"):
        path = "/" + path
    return re.sub(r"/{2,}", "/", path).rstrip("/") or "/"


def path_matches_prefixes(path: str, prefixes: List[str]) -> bool:
    if not prefixes:
        return True

    path = clean_path(path)
    normalized_prefixes = [clean_path(p) for p in prefixes]
    return any(path == prefix or path.startswith(prefix + "/") for prefix in normalized_prefixes)


def contains_any_keyword(text: str, keywords: List[str]) -> bool:
    text = text.lower()
    return any(keyword.lower() in text for keyword in keywords)


def infer_source_metadata(file_path: Path) -> dict:
    source_id = detect_source_id_from_filename(file_path)

    if source_id and source_id in TRUSTED_SOURCES:
        source = TRUSTED_SOURCES[source_id]
        return {
            "source_id": source.source_id,
            "source_label": source.label,
            "domain": source.domain,
            "trust_level": source.trust_level,
            "audience": source.audience,
            "default_topic": source.default_topic,
            "language": source.language,
            "filename": file_path.name,
            "title": file_path.stem.replace("_", " ").strip(),
        }

    return {
        "source_id": "unknown",
        "source_label": "Unknown Source",
        "domain": "unknown",
        "trust_level": "unverified",
        "audience": "unknown",
        "default_topic": "breast_cancer",
        "language": "unknown",
        "filename": file_path.name,
        "title": file_path.stem.replace("_", " ").strip(),
    }


def build_url_document_metadata(
    url: str,
    title: Optional[str] = None,
    extra: Optional[dict] = None,
) -> dict:
    source = find_source_for_url(url)

    parsed = urlparse(url)
    fallback_title = title or Path(parsed.path).stem.replace("-", " ").replace("_", " ").strip()
    fallback_title = fallback_title or parsed.netloc

    if source:
        base = {
            "source_id": source.source_id,
            "source_label": source.label,
            "domain": source.domain,
            "trust_level": source.trust_level,
            "audience": source.audience,
            "default_topic": source.default_topic,
            "language": source.language,
            "url": normalize_url(url),
            "title": fallback_title,
        }
    else:
        base = {
            "source_id": "unknown",
            "source_label": "Unknown Source",
            "domain": parsed.netloc.lower() or "unknown",
            "trust_level": "unverified",
            "audience": "unknown",
            "default_topic": "breast_cancer",
            "language": "unknown",
            "url": normalize_url(url),
            "title": fallback_title,
        }

    if extra:
        base.update(extra)

    return base


def metadata_with_document_fields(file_path: Path, extra: Optional[dict] = None) -> dict:
    base = infer_source_metadata(file_path)
    if extra:
        base.update(extra)
    return base


def get_seed_urls(source_id: Optional[str] = None) -> List[str]:
    if source_id:
        source = TRUSTED_SOURCES.get(source_id)
        return source.seed_urls[:] if source else []

    all_urls: List[str] = []
    for source in TRUSTED_SOURCES.values():
        all_urls.extend(source.seed_urls)
    return all_urls


def is_allowed_url_for_source(url: str, source: SourceDefinition) -> bool:
    try:
        normalized_url = normalize_url(url)
        parsed = urlparse(normalized_url)
    except Exception:
        return False

    if parsed.scheme not in {"http", "https"}:
        return False

    if has_blocked_extension(normalized_url):
        return False

    domain = normalize_domain(parsed.netloc)
    allowed_domains = {normalize_domain(d) for d in source.allowed_domains}
    if domain not in allowed_domains:
        return False

    path = clean_path(parsed.path)
    full_url_lc = normalized_url.lower()

    if path in {clean_path(p) for p in source.blocked_exact_paths}:
        return False

    if contains_any_keyword(full_url_lc, GLOBAL_BLOCKED_URL_KEYWORDS):
        return False

    if contains_any_keyword(full_url_lc, source.blocked_path_keywords):
        return False

    if contains_any_keyword(full_url_lc, GLOBAL_BLOCKED_TOPIC_DRIFT):
        return False

    prefix_ok = path_matches_prefixes(path, source.allowed_path_prefixes)
    keyword_ok = contains_any_keyword(full_url_lc, source.include_url_keywords)
    topic_ok = contains_any_keyword(full_url_lc, GLOBAL_TOPIC_MUST_HAVE)

    # If explicit source rules exist, respect them.
    if source.allowed_path_prefixes and source.include_url_keywords:
        return (prefix_ok or keyword_ok) and topic_ok

    if source.allowed_path_prefixes:
        return prefix_ok and topic_ok

    if source.include_url_keywords:
        return keyword_ok and topic_ok

    return topic_ok


def as_serializable_registry() -> dict:
    return {key: asdict(value) for key, value in TRUSTED_SOURCES.items()}