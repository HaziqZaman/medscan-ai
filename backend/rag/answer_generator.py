from typing import Dict, Optional
import time
import requests

from google.genai import types
from rag.config import (
    GEMINI_API_KEY,
    GEMINI_GENERATION_MODEL,
    DEEPSEEK_API_KEY,
    DEEPSEEK_MODEL,
)

from rag.prompt_builder import (
    build_system_instruction,
    build_user_prompt,
    build_sources_payload,
    infer_response_style,
)

from rag.retriever import hybrid_retrieve
from rag.reranker import rerank_results


# ---------------- GEMINI ----------------
def get_genai_client():
    if not GEMINI_API_KEY:
        return None
    from google import genai
    return genai.Client(api_key=GEMINI_API_KEY)


def generate_with_gemini(prompt: str):
    print("👉 Trying Gemini...")

    client = get_genai_client()
    if not client:
        raise Exception("Gemini not configured")

    for i in range(3):
        try:
            response = client.models.generate_content(
                model=GEMINI_GENERATION_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=build_system_instruction(),
                    temperature=0.45,
                ),
            )

            print("✅ Gemini success")
            return getattr(response, "text", None)

        except Exception as e:
            error_text = str(e)
            print(f"⚠️ Gemini attempt {i+1} failed: {error_text}")

            if "API_KEY_INVALID" in error_text or "API key not valid" in error_text:
                print("❌ Gemini API key invalid, not retrying")
                raise Exception("Gemini invalid API key")

            time.sleep(2 ** i)

    raise Exception("Gemini failed completely")


# ---------------- DEEPSEEK ----------------
def generate_with_deepseek(prompt: str):
    print("👉 Trying DeepSeek...")

    if not DEEPSEEK_API_KEY:
        raise Exception("DeepSeek not configured")

    url = "https://api.deepseek.com/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": build_system_instruction()},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.45,
    }

    response = requests.post(url, headers=headers, json=payload, timeout=20)

    if response.status_code != 200:
        print("❌ DeepSeek failed:", response.text)
        raise Exception("DeepSeek failed")

    print("✅ DeepSeek success")
    data = response.json()
    return data["choices"][0]["message"]["content"]


# ---------------- FALLBACK ----------------
def grounded_fallback(results):
    print("⚠️ Using grounded fallback (no API worked)")

    if not results:
        return "No sufficient information available."

    text = "\n\n".join([r["text"] for r in results[:3]])
    return f"Based on retrieved medical information:\n\n{text}"


# ---------------- MAIN ----------------
def generate_grounded_answer(
    query: str,
    case_summary: Optional[str] = None,
) -> Dict:

    response_style = infer_response_style(query)

    if not query or not query.strip():
        return {"answer": "Please enter a question.", "sources": []}

    retrieval = hybrid_retrieve(query=query)
    initial_results = retrieval.get("results", [])

    if not initial_results:
        return {"answer": "No relevant medical information found.", "sources": []}

    results = rerank_results(query=query, results=initial_results)

    prompt = build_user_prompt(
        query=query,
        retrieved_results=results,
        case_summary=case_summary,
        response_style=response_style,
    )

    # 1️⃣ TRY GEMINI
    try:
        answer = generate_with_gemini(prompt)
        if answer:
            return {
                "answer": answer.strip(),
                "sources": build_sources_payload(results),
            }
    except Exception:
        print("➡️ Gemini failed, switching to DeepSeek...")

    # 2️⃣ TRY DEEPSEEK
    try:
        answer = generate_with_deepseek(prompt)
        if answer:
            return {
                "answer": answer.strip(),
                "sources": build_sources_payload(results),
            }
    except Exception:
        print("➡️ DeepSeek also failed")

    # 3️⃣ FINAL FALLBACK
    return {
        "answer": grounded_fallback(results),
        "sources": build_sources_payload(results),
    }