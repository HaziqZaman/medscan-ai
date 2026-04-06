import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    )
}

TOPIC_SPECS = [
    {
        "id": 1,
        "category": "Basics",
        "subcategory": "Overview",
        "title": "What is Breast Cancer?",
        "source": "National Cancer Institute",
        "sourceUrl": "https://www.cancer.gov/types/breast/what-is-breast-cancer",
        "matchTerms": ["breast cancer", "starts in the breast", "ducts", "lobules"],
    },
    {
        "id": 2,
        "category": "Basics",
        "subcategory": "Anatomy",
        "title": "Breast Anatomy",
        "source": "SEER Training",
        "sourceUrl": "https://training.seer.cancer.gov/breast/anatomy.html",
        "matchTerms": ["lobes", "lobules", "ducts", "breast is made up"],
    },
    {
        "id": 3,
        "category": "Types",
        "subcategory": "Overview",
        "title": "Breast Cancer Types",
        "source": "National Cancer Institute",
        "sourceUrl": "https://www.cancer.gov/types/breast/breast-cancer-types",
        "matchTerms": ["types of breast cancer", "invasive", "ductal", "lobular"],
    },
    {
        "id": 4,
        "category": "Types",
        "subcategory": "Invasive",
        "title": "Invasive Ductal Carcinoma (IDC)",
        "source": "SEER Training",
        "sourceUrl": "https://training.seer.cancer.gov/breast/types.html",
        "matchTerms": ["invasive ductal carcinoma", "ductal carcinoma", "70%"],
    },
    {
        "id": 5,
        "category": "Types",
        "subcategory": "Invasive",
        "title": "Invasive Lobular Carcinoma (ILC)",
        "source": "SEER Training",
        "sourceUrl": "https://training.seer.cancer.gov/breast/types.html",
        "matchTerms": ["lobular carcinoma", "invasive lobular", "lobules"],
    },
    {
        "id": 6,
        "category": "Types",
        "subcategory": "Subtype",
        "title": "Triple-Negative Breast Cancer",
        "source": "SEER",
        "sourceUrl": "https://seer.cancer.gov/statfacts/html/breast-subtypes.html",
        "matchTerms": ["HR-/HER2-", "subtypes", "triple-negative"],
    },
    {
        "id": 7,
        "category": "Types",
        "subcategory": "Subtype",
        "title": "HER2-Positive Breast Cancer",
        "source": "SEER",
        "sourceUrl": "https://seer.cancer.gov/statfacts/html/breast-subtypes.html",
        "matchTerms": ["HER2", "HR+/HER2+", "HR-/HER2+"],
    },
    {
        "id": 8,
        "category": "Symptoms & Risk",
        "subcategory": "Symptoms",
        "title": "Symptoms of Breast Cancer",
        "source": "American Cancer Society",
        "sourceUrl": "https://www.cancer.org/cancer/types/breast-cancer/screening-tests-and-early-detection/breast-cancer-signs-and-symptoms.html",
        "matchTerms": ["symptoms", "lump", "nipple", "skin changes"],
    },
    {
        "id": 9,
        "category": "Symptoms & Risk",
        "subcategory": "Risk Factors",
        "title": "Risk Factors for Breast Cancer",
        "source": "National Cancer Institute",
        "sourceUrl": "https://www.cancer.gov/types/breast/risk-fact-sheet",
        "matchTerms": ["risk", "BRCA", "family history", "lifetime"],
    },
    {
        "id": 10,
        "category": "Symptoms & Risk",
        "subcategory": "Causes & Genetics",
        "title": "Causes and Genetics",
        "source": "National Cancer Institute",
        "sourceUrl": "https://www.cancer.gov/types/breast/causes-risk-factors",
        "matchTerms": ["BRCA1", "BRCA2", "genetic", "family history", "PALB2"],
    },
    {
        "id": 11,
        "category": "Diagnosis",
        "subcategory": "Screening",
        "title": "Screening and Early Detection",
        "source": "National Cancer Institute",
        "sourceUrl": "https://www.cancer.gov/types/breast/screening",
        "matchTerms": ["screening", "mammogram", "early detection"],
    },
    {
        "id": 12,
        "category": "Diagnosis",
        "subcategory": "Diagnosis",
        "title": "Breast Cancer Diagnosis",
        "source": "National Cancer Institute",
        "sourceUrl": "https://www.cancer.gov/types/breast/diagnosis",
        "matchTerms": ["diagnosis", "biopsy", "imaging", "pathology"],
    },
    {
        "id": 13,
        "category": "Histopathology",
        "subcategory": "Pathology",
        "title": "Breast Pathology Basics",
        "source": "SEER Training",
        "sourceUrl": "https://training.seer.cancer.gov/breast/pathology/",
        "matchTerms": ["pathology", "microscope", "tissue", "histology"],
    },
    {
        "id": 14,
        "category": "Histopathology",
        "subcategory": "Slide Interpretation",
        "title": "Reading Histopathology Images",
        "source": "SEER Training",
        "sourceUrl": "https://training.seer.cancer.gov/breast/pathology/",
        "matchTerms": ["cells", "tissue", "microscope", "pathology"],
    },
    {
        "id": 15,
        "category": "Staging & Grading",
        "subcategory": "Grading",
        "title": "Tumor Grading",
        "source": "National Cancer Institute",
        "sourceUrl": "https://www.cancer.gov/publications/dictionaries/cancer-terms/def/tumor-grade",
        "matchTerms": ["tumor grade", "grade", "abnormal"],
    },
    {
        "id": 16,
        "category": "Staging & Grading",
        "subcategory": "Staging",
        "title": "Breast Cancer Staging",
        "source": "National Cancer Institute",
        "sourceUrl": "https://www.cancer.gov/types/breast/stages",
        "matchTerms": ["stage", "TNM", "lymph nodes", "biomarkers"],
    },
    {
        "id": 17,
        "category": "Treatment",
        "subcategory": "Overview",
        "title": "Breast Cancer Treatment Overview",
        "source": "National Cancer Institute",
        "sourceUrl": "https://www.cancer.gov/types/breast/treatment",
        "matchTerms": ["treatment", "surgery", "radiation", "chemotherapy", "hormone therapy"],
    },
    {
        "id": 18,
        "category": "AI in MedScan",
        "subcategory": "Model",
        "title": "How the AI Model Works",
        "manual": True,
        "summary": "How MedScan AI analyzes histopathology image patches.",
        "description": [
            "MedScan AI uses a deep learning model based on ResNet-18 to analyze breast histopathology image patches. The model learns visual patterns associated with cancerous and non-cancerous tissue from labeled training examples.",
            "When a user uploads an image patch, the model processes the image and produces a predicted class along with a confidence score. This makes the system useful as an educational aid for understanding AI-assisted pathology workflows.",
            "The model is designed for learning support, not clinical diagnosis. Its purpose in the system is to help students explore how image-based cancer classification works in practice."
        ],
        "keywords": ["AI", "ResNet-18", "classification", "histopathology"],
        "source": "MedScan AI",
        "sourceUrl": "",
    },
    {
        "id": 19,
        "category": "AI in MedScan",
        "subcategory": "Explainability",
        "title": "Grad-CAM Explained",
        "manual": True,
        "summary": "How MedScan AI highlights image regions behind a prediction.",
        "description": [
            "Grad-CAM is an explainability method that highlights the regions of an image that most strongly influenced the model’s prediction. It creates a heatmap based on gradient information from deep layers of the neural network.",
            "In MedScan AI, Grad-CAM helps users see which tissue regions were most relevant to the model when identifying possible cancer-related patterns. This makes the result easier to interpret.",
            "The heatmap does not replace expert review, but it improves transparency and helps learners understand how explainable AI supports image analysis."
        ],
        "keywords": ["Grad-CAM", "heatmap", "explainability", "AI"],
        "source": "MedScan AI",
        "sourceUrl": "",
    },
]

SKIP_PHRASES = [
    "last reviewed",
    "print",
    "email",
    "facebook",
    "twitter",
    "this page",
    "more information",
    "learn more",
    "clinical trial",
    "credit:",
    "enlarge image",
    "was this page helpful",
]

OUTPUT_PATH = Path(__file__).resolve().parents[1] / "data" / "knowledgeTopics.js"

URL_CACHE = {}

SESSION = requests.Session()
retry_strategy = Retry(
    total=2,
    connect=2,
    read=2,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"],
)
adapter = HTTPAdapter(max_retries=retry_strategy)
SESSION.mount("http://", adapter)
SESSION.mount("https://", adapter)
SESSION.headers.update(HEADERS)


def clean_text(text: str) -> str:
    text = re.sub(r"\[[0-9]+\]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def valid_paragraph(text: str) -> bool:
    if len(text) < 80:
        return False

    lower = text.lower()
    for phrase in SKIP_PHRASES:
        if phrase in lower:
            return False

    return True


def normalize_url(url: str) -> str:
    return url.rstrip("/")


def fetch_paragraphs(url: str) -> list[str]:
    cache_key = normalize_url(url)

    if cache_key in URL_CACHE:
        print(f"Using cache: {url}", flush=True)
        return URL_CACHE[cache_key]

    response = SESSION.get(url, timeout=(5, 10), allow_redirects=True)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
        tag.decompose()

    main = soup.find("main") or soup.find("article") or soup.body
    raw_paragraphs = main.find_all("p") if main else []

    paragraphs = []
    seen = set()

    for p in raw_paragraphs:
        text = clean_text(p.get_text(" ", strip=True))
        if not valid_paragraph(text):
            continue
        if text in seen:
            continue
        seen.add(text)
        paragraphs.append(text)

    URL_CACHE[cache_key] = paragraphs
    return paragraphs


def score_paragraph(text: str, match_terms: list[str]) -> int:
    lower = text.lower()
    score = 0
    for term in match_terms:
        if term.lower() in lower:
            score += 2
    return score


def pick_description(paragraphs: list[str], match_terms: list[str]) -> list[str]:
    if not paragraphs:
        return [
            "Content could not be extracted automatically from the selected source.",
            "Review the source page manually and update this topic if needed.",
            "This generated entry is only a fallback and should be checked before final submission."
        ]

    scored = []
    for index, paragraph in enumerate(paragraphs):
        scored.append((score_paragraph(paragraph, match_terms), index, paragraph))

    matched = [item for item in scored if item[0] > 0]

    if matched:
        matched.sort(key=lambda x: (-x[0], x[1]))
        chosen = [item[2] for item in matched[:3]]
    else:
        chosen = paragraphs[:3]

    final_paragraphs = []
    seen = set()

    for para in chosen:
        trimmed = para[:700].strip()
        if trimmed not in seen:
            seen.add(trimmed)
            final_paragraphs.append(trimmed)

    for para in paragraphs:
        if len(final_paragraphs) >= 3:
            break
        trimmed = para[:700].strip()
        if trimmed not in seen:
            seen.add(trimmed)
            final_paragraphs.append(trimmed)

    return final_paragraphs[:3]


def make_summary(description: list[str]) -> str:
    if not description:
        return "No summary available."

    first = description[0]
    sentence = re.split(r"(?<=[.!?])\s+", first)[0].strip()

    if len(sentence) > 150:
        sentence = sentence[:147].rstrip() + "..."

    return sentence


def make_keywords(topic: dict, description: list[str]) -> list[str]:
    base = [
        topic["category"],
        topic["subcategory"],
        topic["title"],
    ]

    words = []

    for item in base:
        for word in re.findall(r"[A-Za-z0-9\-\+]+", item):
            lower = word.lower()
            if len(lower) >= 3 and lower not in words:
                words.append(lower)

    if description:
        extra_words = re.findall(r"[A-Za-z0-9\-\+]+", " ".join(description[:2]))
        for word in extra_words:
            lower = word.lower()
            if len(lower) >= 5 and lower not in words:
                words.append(lower)
            if len(words) >= 8:
                break

    return words[:8]


def build_topic(topic: dict) -> dict:
    if topic.get("manual"):
        return {
            "id": topic["id"],
            "category": topic["category"],
            "subcategory": topic["subcategory"],
            "title": topic["title"],
            "summary": topic["summary"],
            "description": topic["description"],
            "keywords": topic["keywords"],
            "source": topic["source"],
            "sourceUrl": topic["sourceUrl"],
        }

    print(f"Fetching: {topic['title']} -> {topic['sourceUrl']}", flush=True)
    paragraphs = fetch_paragraphs(topic["sourceUrl"])
    description = pick_description(paragraphs, topic["matchTerms"])
    summary = make_summary(description)
    keywords = make_keywords(topic, description)

    return {
        "id": topic["id"],
        "category": topic["category"],
        "subcategory": topic["subcategory"],
        "title": topic["title"],
        "summary": summary,
        "description": description,
        "keywords": keywords,
        "source": topic["source"],
        "sourceUrl": topic["sourceUrl"],
    }


def format_js(topics: list[dict]) -> str:
    return "const TOPICS = " + json.dumps(topics, indent=2, ensure_ascii=False) + ";\n\nexport default TOPICS;\n"


def main():
    built_topics = []

    for topic in TOPIC_SPECS:
        try:
            built = build_topic(topic)
            built_topics.append(built)
            print(f"[OK] {topic['title']}", flush=True)
        except Exception as exc:
            print(f"[ERROR] {topic['title']}: {exc}", flush=True)
            built_topics.append({
                "id": topic["id"],
                "category": topic["category"],
                "subcategory": topic["subcategory"],
                "title": topic["title"],
                "summary": "Automatic extraction failed for this topic.",
                "description": [
                    "The source could not be processed automatically during generation.",
                    "Check the source URL or update the extraction rules for this topic.",
                    f"Error details: {str(exc)}"
                ],
                "keywords": [topic["category"].lower(), topic["subcategory"].lower()],
                "source": topic.get("source", ""),
                "sourceUrl": topic.get("sourceUrl", ""),
            })

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(format_js(built_topics), encoding="utf-8")
    print(f"\nDone. Generated file: {OUTPUT_PATH}", flush=True)


if __name__ == "__main__":
    main()