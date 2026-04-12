from typing import Dict, Optional

from google.genai import types

from rag.config import GEMINI_API_KEY, GEMINI_GENERATION_MODEL
from rag.guardrails import (
    classify_query,
    greeting_response,
    out_of_scope_response,
)
from rag.prompt_builder import (
    build_system_instruction,
    build_user_prompt,
    build_sources_payload,
)
from rag.retriever import hybrid_retrieve
from rag.reranker import rerank_results


MIN_TOP_SCORE = 0.12
MIN_SECONDARY_SCORE = 0.08
MIN_STRONG_RESULTS = 2


def get_genai_client():
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found. Check backend/.env")

    from google import genai
    return genai.Client(api_key=GEMINI_API_KEY)


def not_enough_grounded_info_response() -> str:
    return (
        "I do not have enough grounded medical information in the current knowledge base "
        "to answer this confidently."
    )


def has_sufficient_grounding(results: list[Dict]) -> bool:
    if not results:
        return False

    top_score = results[0].get("combined_score", 0.0)
    strong_results = sum(
        1 for item in results[:3]
        if item.get("combined_score", 0.0) >= MIN_SECONDARY_SCORE
    )

    return top_score >= MIN_TOP_SCORE or strong_results >= MIN_STRONG_RESULTS


def generate_grounded_answer(
    query: str,
    case_summary: Optional[str] = None,
) -> Dict:
    scope_result = classify_query(query)

    if scope_result["scope"] == "greeting":
        return {
            "scope": scope_result["scope"],
            "reason": scope_result["reason"],
            "answer": greeting_response(),
            "sources": [],
            "retrieved_count": 0,
        }

    if scope_result["scope"] == "out_of_scope":
        return {
            "scope": scope_result["scope"],
            "reason": scope_result["reason"],
            "answer": out_of_scope_response(),
            "sources": [],
            "retrieved_count": 0,
        }

    retrieval = hybrid_retrieve(query=query)
    initial_results = retrieval.get("results", [])

    if not initial_results:
        return {
            "scope": scope_result["scope"],
            "reason": "no_retrieval_results",
            "answer": not_enough_grounded_info_response(),
            "sources": [],
            "retrieved_count": 0,
        }

    if not has_sufficient_grounding(initial_results):
        return {
            "scope": scope_result["scope"],
            "reason": "weak_retrieval_grounding",
            "answer": not_enough_grounded_info_response(),
            "sources": [],
            "retrieved_count": len(initial_results),
        }

    results = rerank_results(query=query, results=initial_results)

    if not results:
        return {
            "scope": scope_result["scope"],
            "reason": "reranker_returned_no_results",
            "answer": not_enough_grounded_info_response(),
            "sources": [],
            "retrieved_count": 0,
        }

    user_prompt = build_user_prompt(
        query=query,
        retrieved_results=results,
        case_summary=case_summary,
    )

    client = get_genai_client()

    response = client.models.generate_content(
        model=GEMINI_GENERATION_MODEL,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=build_system_instruction(),
            temperature=0.2,
        ),
    )

    answer_text = getattr(response, "text", None)
    if not answer_text:
        answer_text = "I could not generate a final grounded answer."

    return {
        "scope": scope_result["scope"],
        "reason": "grounded_answer_generated",
        "answer": answer_text.strip(),
        "sources": build_sources_payload(results),
        "retrieved_count": len(results),
        "retrieved_results": results,
    }


def main():
    query = "What is invasive ductal carcinoma?"
    result = generate_grounded_answer(query=query)

    print("\n" + "=" * 100)
    print("FINAL ANSWER")
    print("=" * 100)
    print(result["answer"])

    print("\nSOURCES")
    print("-" * 100)
    for item in result["sources"]:
        print(f"- {item['title']} ({item['source']}) | {item['chunk_id']}")

    print(f"\nRetrieved Count: {result['retrieved_count']}")
    print(f"Scope: {result['scope']}")
    print(f"Reason: {result['reason']}")


if __name__ == "__main__":
    main()