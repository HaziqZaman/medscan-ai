from typing import Dict, Optional

from google.genai import types

from rag.config import GEMINI_API_KEY, GEMINI_GENERATION_MODEL
from rag.prompt_builder import (
    build_system_instruction,
    build_user_prompt,
    build_sources_payload,
    infer_response_style,
)
from rag.retriever import hybrid_retrieve
from rag.reranker import rerank_results


MIN_TOP_SCORE = 0.12
MIN_SECONDARY_SCORE = 0.08
MIN_STRONG_RESULTS = 2

MEDICAL_SCOPE_HINTS = {
    "breast", "cancer", "carcinoma", "idc", "dcis", "ilc", "tumor", "tumour",
    "pathology", "histopathology", "biopsy", "stage", "staging", "grade", "grading",
    "metastasis", "metastatic", "lymph", "her2", "mammogram", "ultrasound",
    "chemotherapy", "radiotherapy", "hormone", "oncology", "case", "analysis",
    "result", "medscan", "receptor",
}

META_CAPABILITY_HINTS = {
    "what can you do",
    "how do you work",
    "what do you do",
    "who are you",
    "what is this project",
    "explain this project",
    "what is medscan ai",
}


def get_genai_client():
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found. Check backend/.env")

    from google import genai
    return genai.Client(api_key=GEMINI_API_KEY)


def not_enough_grounded_info_response(style: str) -> str:
    if style == "urdu_script":
        return (
            "میرے پاس موجود grounded medical information اس سوال کا "
            "اعتماد کے ساتھ جواب دینے کے لیے کافی نہیں ہے۔"
        )

    if style == "roman_urdu":
        return (
            "Mere paas mojood grounded medical information is sawal ka "
            "aitemaad ke sath jawab dene ke liye kafi nahi hai."
        )

    return (
        "I do not have enough grounded medical information in the current knowledge base "
        "to answer this confidently."
    )


def capability_response(style: str) -> str:
    if style == "urdu_script":
        return (
            "میں breast cancer education, pathology concepts, aur MedScan AI case explanations "
            "میں مدد کر سکتا ہوں۔ آپ IDC, DCIS, biopsy, grading, staging, HER2, "
            "یا اپنی latest saved case کے بارے میں سوال پوچھ سکتے ہیں۔"
        )

    if style == "roman_urdu":
        return (
            "Main breast cancer education, pathology concepts, aur MedScan AI case explanations "
            "mein madad kar sakta hoon. Aap IDC, DCIS, biopsy, grading, staging, HER2, "
            "ya apni latest saved case ke bare mein sawal pooch sakte hain."
        )

    return (
        "I can help with breast-cancer education, pathology concepts, and MedScan AI case explanations. "
        "You can ask about IDC, DCIS, biopsy, grading, staging, HER2, or your latest saved case."
    )


def scope_bound_response(style: str) -> str:
    if style == "urdu_script":
        return (
            "میں صرف breast cancer education، pathology، cancer-study "
            "اور MedScan AI case-related سوالات میں مدد کر سکتا ہوں۔"
        )

    if style == "roman_urdu":
        return (
            "Main sirf breast cancer education, pathology, cancer-study, "
            "aur MedScan AI case-related sawalat mein madad kar sakta hoon."
        )

    return (
        "I can only help with breast-cancer education, pathology, cancer-study, "
        "and MedScan AI case-related questions."
    )


def generation_temporarily_unavailable_response(style: str) -> str:
    if style == "urdu_script":
        return (
            "Grounded information mil gayi تھی، لیکن final response generation temporarily unavailable hai. "
            "براہِ کرم دوبارہ کوشش کریں۔"
        )

    if style == "roman_urdu":
        return (
            "Grounded information mil gayi thi, lekin final response generation temporarily unavailable hai. "
            "Please thori dair baad dobara try karein."
        )

    return (
        "Grounded information was retrieved, but final response generation is temporarily unavailable. "
        "Please try again shortly."
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


def looks_like_meta_capability_query(query: str) -> bool:
    lowered = (query or "").strip().lower()
    return any(phrase in lowered for phrase in META_CAPABILITY_HINTS)


def looks_medical_or_case_query(query: str, case_summary: Optional[str] = None) -> bool:
    lowered = (query or "").lower()

    if case_summary:
        case_words = {"case", "result", "analysis", "latest", "previous", "saved"}
        if any(word in lowered for word in case_words):
            return True

    return any(term in lowered for term in MEDICAL_SCOPE_HINTS)


def weak_or_empty_retrieval_response(
    query: str,
    response_style: str,
    case_summary: Optional[str] = None,
) -> Dict:
    if looks_like_meta_capability_query(query):
        return {
            "scope": "meta_capability",
            "reason": "capability_query_without_retrieval",
            "answer": capability_response(response_style),
            "sources": [],
            "retrieved_count": 0,
        }

    if looks_medical_or_case_query(query, case_summary):
        return {
            "scope": "medical_insufficient",
            "reason": "weak_or_empty_retrieval_for_medical_query",
            "answer": not_enough_grounded_info_response(response_style),
            "sources": [],
            "retrieved_count": 0,
        }

    return {
        "scope": "out_of_scope",
        "reason": "non_medical_or_unsupported_query",
        "answer": scope_bound_response(response_style),
        "sources": [],
        "retrieved_count": 0,
    }


def generate_grounded_answer(
    query: str,
    case_summary: Optional[str] = None,
) -> Dict:
    response_style = infer_response_style(query)

    if not query or not query.strip():
        return {
            "scope": "invalid",
            "reason": "empty_query",
            "answer": "Please enter a question.",
            "sources": [],
            "retrieved_count": 0,
        }

    retrieval = hybrid_retrieve(query=query)
    initial_results = retrieval.get("results", [])

    if not initial_results:
        return weak_or_empty_retrieval_response(query, response_style, case_summary)

    if not has_sufficient_grounding(initial_results):
        fallback = weak_or_empty_retrieval_response(query, response_style, case_summary)
        fallback["retrieved_count"] = len(initial_results)
        return fallback

    results = rerank_results(query=query, results=initial_results)

    if not results:
        return weak_or_empty_retrieval_response(query, response_style, case_summary)

    user_prompt = build_user_prompt(
        query=query,
        retrieved_results=results,
        case_summary=case_summary,
        response_style=response_style,
    )

    client = get_genai_client()

    try:
        response = client.models.generate_content(
            model=GEMINI_GENERATION_MODEL,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=build_system_instruction(),
                temperature=0.45,
            ),
        )
    except Exception:
        return {
            "scope": "generation_unavailable",
            "reason": "gemini_generation_failure",
            "answer": generation_temporarily_unavailable_response(response_style),
            "sources": [],
            "retrieved_count": len(results),
        }

    answer_text = getattr(response, "text", None)
    if not answer_text:
        answer_text = "I could not generate a final grounded answer."

    return {
        "scope": "grounded_medical_answer",
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