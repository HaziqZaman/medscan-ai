from typing import Dict
import re


CASE_HINTS = {
    "my case",
    "my latest case",
    "my previous case",
    "my result",
    "my latest result",
    "my previous result",
    "my analysis",
    "my last analysis",
    "latest case",
    "previous case",
    "explain my case",
    "explain my latest case",
    "latest analysis",
    "last analysis",
}

GREETING_HINTS = {
    "hi",
    "hello",
    "hey",
    "hy",
    "salam",
    "assalamualaikum",
    "assalamu alaikum",
    "aoa",
    "good morning",
    "good afternoon",
    "good evening",
}

# This is now intentionally small and explicit.
# We only block prompts that are clearly unrelated to the chatbot's purpose.
OUT_OF_SCOPE_HINTS = {
    "weather",
    "temperature",
    "football",
    "cricket",
    "movie",
    "movies",
    "song",
    "songs",
    "joke",
    "memes",
    "politics",
    "election",
    "travel plan",
    "vacation",
    "javascript",
    "react bug",
    "python error",
    "coding bug",
    "debug my code",
    "fix my code",
    "programming help",
    "stock market",
    "crypto",
    "bitcoin",
    "relationship advice",
    "love advice",
}

# This is NOT used to gate medical queries.
# It is only used to avoid blocking a mixed query too aggressively.
MEDICAL_OVERRIDE_HINTS = {
    "breast",
    "cancer",
    "tumor",
    "tumour",
    "carcinoma",
    "oncology",
    "histopathology",
    "pathology",
    "biopsy",
    "idc",
    "dcis",
    "ilc",
    "grading",
    "grade",
    "staging",
    "stage",
    "lymph",
    "metastasis",
    "mammogram",
    "ultrasound",
    "chemotherapy",
    "radiotherapy",
    "her2",
    "receptor",
    "nuclei",
    "mitosis",
    "medscan",
}


def normalize_text(text: str) -> str:
    cleaned = re.sub(r"[^a-z0-9\s]+", " ", text.lower())
    return " ".join(cleaned.strip().split())


def contains_any_phrase(text: str, phrases: set[str]) -> bool:
    return any(phrase in text for phrase in phrases)


def is_case_context_query(normalized: str) -> bool:
    return contains_any_phrase(normalized, CASE_HINTS)


def is_simple_greeting(normalized: str) -> bool:
    return normalized in GREETING_HINTS


def has_medical_override_signal(normalized: str) -> bool:
    return contains_any_phrase(normalized, MEDICAL_OVERRIDE_HINTS)


def is_obviously_out_of_scope(normalized: str) -> bool:
    if is_case_context_query(normalized):
        return False

    if has_medical_override_signal(normalized):
        return False

    return contains_any_phrase(normalized, OUT_OF_SCOPE_HINTS)


def classify_query(query: str) -> Dict[str, str]:
    normalized = normalize_text(query)

    if not normalized:
        return {
            "scope": "invalid",
            "reason": "empty_query",
        }

    if is_case_context_query(normalized):
        return {
            "scope": "case_context",
            "reason": "matched_case_hint",
        }

    if is_simple_greeting(normalized):
        return {
            "scope": "greeting",
            "reason": "simple_greeting",
        }

    if is_obviously_out_of_scope(normalized):
        return {
            "scope": "out_of_scope",
            "reason": "matched_obvious_non_medical_hint",
        }

    # Default is allow-to-retrieval, not reject.
    return {
        "scope": "general",
        "reason": "allow_to_retrieval",
    }


def allow_query(query: str) -> bool:
    result = classify_query(query)
    return result["scope"] not in {"invalid", "out_of_scope"}


def greeting_response() -> str:
    return (
        "Hello — I can help with breast cancer education, pathology concepts, "
        "and MedScan AI case explanations. You can ask about IDC, grading, staging, "
        "biopsy, treatment basics, or say 'explain my latest case'."
    )


def out_of_scope_response() -> str:
    return (
        "This chatbot is limited to breast-cancer education, pathology topics, "
        "and MedScan AI case-related questions."
    )