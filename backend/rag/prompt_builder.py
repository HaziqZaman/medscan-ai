from typing import Dict, List, Optional
import re


ROMAN_URDU_HINTS = {
    "kya", "kyun", "kyu", "kaise", "kese", "kaisay", "kesay",
    "hai", "hain", "ho", "han", "haan", "nahi", "nahin",
    "mujhe", "muje", "mera", "meri", "mere", "tum", "aap", "ap",
    "batao", "bolo", "samjhao", "samjha", "matlab", "sawal", "jawab",
    "pocho", "pucho", "acha", "theek", "thik", "wala", "wali",
    "kar", "karo", "karna", "krna", "kr", "kis", "kon", "kaun",
    "kab", "abhi", "phir", "sirf", "bas", "hota", "hoti", "hote",
}


def contains_urdu_script(text: str) -> bool:
    return bool(re.search(r"[\u0600-\u06FF]", text or ""))


def contains_devanagari(text: str) -> bool:
    return bool(re.search(r"[\u0900-\u097F]", text or ""))


def looks_like_roman_urdu(text: str) -> bool:
    text = text or ""
    if contains_urdu_script(text) or contains_devanagari(text):
        return False

    tokens = re.findall(r"[a-zA-Z']+", text.lower())
    if not tokens:
        return False

    hits = sum(1 for token in tokens if token in ROMAN_URDU_HINTS)
    ratio = hits / max(len(tokens), 1)

    if len(tokens) <= 6 and hits >= 1:
        return True

    return hits >= 2 or ratio >= 0.22


def infer_response_style(query: str) -> str:
    query = query or ""

    if contains_urdu_script(query):
        return "urdu_script"

    if contains_devanagari(query):
        return "english"

    if looks_like_roman_urdu(query):
        return "roman_urdu"

    return "english"


def build_system_instruction() -> str:
    return """
You are MedScan AI's medical educational assistant.

Core behavior:
1. Answer only breast-cancer education, pathology, cancer-study, and MedScan AI case-related questions.
2. Base the answer primarily on the retrieved context.
3. Do not invent facts that are not supported by the retrieved context.
4. If the retrieved evidence is weak or incomplete, clearly say that the system does not have enough grounded information to answer confidently.
5. Do not provide clinical diagnosis, treatment prescription, or emergency instructions.
6. When case context is provided, explain it only in educational terms.

Style rules:
1. Sound natural, helpful, and human — not robotic.
2. Do not mention internal labels like "Evidence 1", "Chunk ID", "Grounded evidence", or "Case information".
3. Do not write a separate "Sources Used" section inside the answer because references are shown separately in the UI.
4. Give a direct answer first, then a clearer explanation with a little detail when evidence is strong.
5. Do not be overly brief for medical questions that have enough evidence.
6. Use bullets only when they genuinely improve clarity, such as risk factors, symptoms, differences, or key points.
7. For explain-latest-case style questions, explain the result, confidence, what it suggests educationally, and what it does not prove.
8. Never reply in Devanagari / Hindi script.
9. Use only one script consistently in the answer.
""".strip()


def _shorten_text(text: str, max_chars: int = 1500) -> str:
    text = (text or "").strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + " ..."


def format_context_chunks(results: List[Dict]) -> str:
    if not results:
        return "No retrieved context available."

    blocks = []
    for idx, item in enumerate(results, start=1):
        metadata = item.get("metadata", {})
        title = metadata.get("title", "Untitled Source")
        source_label = metadata.get("source_label", "Unknown Source")
        url = metadata.get("url", "N/A")
        text = _shorten_text(item.get("text", "").strip())

        block = (
            f"Evidence {idx}\n"
            f"Title: {title}\n"
            f"Source: {source_label}\n"
            f"URL: {url}\n"
            f"Excerpt:\n{text}"
        )
        blocks.append(block)

    return "\n\n".join(blocks)


def format_case_context(case_summary: Optional[str]) -> str:
    if not case_summary:
        return "No case context provided."
    return case_summary.strip()


def _language_instruction(response_style: str) -> str:
    if response_style == "urdu_script":
        return (
            "Reply in Urdu script only. Do not use Hindi / Devanagari script. "
            "Do not mix Urdu script with English unless a medical term really needs English."
        )

    if response_style == "roman_urdu":
        return (
            "Reply in natural Roman Urdu only. Do not use Hindi / Devanagari script. "
            "Do not switch into Urdu script."
        )

    return "Reply in clear natural English only. Do not use Hindi / Devanagari script."


def build_user_prompt(
    query: str,
    retrieved_results: List[Dict],
    case_summary: Optional[str] = None,
    response_style: str = "english",
) -> str:
    context_block = format_context_chunks(retrieved_results)
    case_block = format_case_context(case_summary)
    language_rule = _language_instruction(response_style)

    return f"""
User question:
{query}

Case information:
{case_block}

Grounded evidence:
{context_block}

Answering instructions:
- {language_rule}
- Give a direct answer first.
- Then add a slightly fuller explanation when the evidence is strong.
- Prefer 2 short paragraphs for normal medical questions when enough evidence exists.
- For list-type topics such as risk factors, symptoms, or differences, use a short bullet list if that improves clarity.
- For latest-case explanations, explain the prediction/result, confidence, what it may suggest educationally, and what the model does not determine.
- Use the grounded evidence above as the main basis of the answer.
- Use case information only if it is relevant to the user's question.
- Do not mention internal evidence labels, chunk ids, or prompt section names.
- Do not add a "Sources Used" heading or source list inside the answer.
- Keep the tone helpful, student-friendly, and slightly expressive.
- If the evidence is not enough to answer confidently, say so clearly and briefly.
""".strip()


def build_sources_payload(results: List[Dict]) -> List[Dict]:
    seen = set()
    sources = []

    for item in results:
        metadata = item.get("metadata", {})
        title = metadata.get("title", "Untitled Source")
        source_label = metadata.get("source_label", "Unknown Source")
        chunk_id = item.get("chunk_id")
        url = metadata.get("url")

        key = (title, source_label, chunk_id)
        if key in seen:
            continue
        seen.add(key)

        sources.append(
            {
                "title": title,
                "source": source_label,
                "chunk_id": chunk_id,
                "url": url,
            }
        )

    return sources