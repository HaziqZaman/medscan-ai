from typing import Dict, List, Optional


def build_system_instruction() -> str:
    return """
You are the MedScan AI medical educational assistant.

Rules:
1. Answer only medical, cancer-study, and MedScan AI case-related questions.
2. Use the retrieved source context as the primary basis of the answer.
3. Do not invent facts that are not supported by the retrieved context.
4. If the retrieved context is weak or insufficient, clearly say that the system does not have enough grounded information.
5. Do not provide clinical diagnosis, treatment prescription, or emergency instructions.
6. Keep answers clear, structured, and student-friendly.
7. When case context is provided, explain it only in educational terms.
8. Mention the difference between general medical explanation and case-specific explanation when relevant.
""".strip()


def format_context_chunks(results: List[Dict]) -> str:
    if not results:
        return "No retrieved context available."

    blocks = []
    for idx, item in enumerate(results, start=1):
        metadata = item.get("metadata", {})
        title = metadata.get("title", "Untitled Source")
        source_label = metadata.get("source_label", "Unknown Source")
        text = item.get("text", "").strip()

        block = (
            f"[Source {idx}]\n"
            f"Title: {title}\n"
            f"Source: {source_label}\n"
            f"Chunk ID: {item.get('chunk_id', 'N/A')}\n"
            f"Content:\n{text}"
        )
        blocks.append(block)

    return "\n\n".join(blocks)


def format_case_context(case_summary: Optional[str]) -> str:
    if not case_summary:
        return "No case context provided."
    return case_summary.strip()


def build_user_prompt(
    query: str,
    retrieved_results: List[Dict],
    case_summary: Optional[str] = None,
) -> str:
    context_block = format_context_chunks(retrieved_results)
    case_block = format_case_context(case_summary)

    return f"""
User Query:
{query}

Case Context:
{case_block}

Retrieved Medical Context:
{context_block}

Instructions:
- Answer the user in clear educational language.
- Base the answer on the retrieved medical context.
- Use case context only if it is provided and relevant.
- Do not make unsupported claims.
- Keep the answer concise but meaningful.
- End with a short section titled "Sources Used" listing the source titles.
""".strip()


def build_sources_payload(results: List[Dict]) -> List[Dict]:
    seen = set()
    sources = []

    for item in results:
        metadata = item.get("metadata", {})
        title = metadata.get("title", "Untitled Source")
        source_label = metadata.get("source_label", "Unknown Source")
        chunk_id = item.get("chunk_id")

        key = (title, source_label, chunk_id)
        if key in seen:
            continue
        seen.add(key)

        sources.append(
            {
                "title": title,
                "source": source_label,
                "chunk_id": chunk_id,
            }
        )

    return sources