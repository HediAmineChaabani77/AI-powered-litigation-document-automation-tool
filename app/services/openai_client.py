"""OpenAI API integration for generating litigation responses."""

import json

from openai import AsyncOpenAI, AuthenticationError, APIConnectionError, RateLimitError

from app.config import settings

_client: AsyncOpenAI | None = None


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.openai_api_key.strip())
    return _client


SYSTEM_PROMPT = """You are an elite litigation support assistant used by top-tier law firms. Your role is to:
1. Analyze legal discovery requests (interrogatories, requests for production, requests for admission).
2. Generate clear, professionally worded draft responses with proper legal formatting.
3. Identify ALL potential objections with legal basis citations (relevance, overbreadth, vagueness, privilege, undue burden, proportionality, attorney-client privilege, work product doctrine, etc.).
4. Flag requests that may need attorney review and explain why.

CRITICAL RULES:
- NEVER ask for clarification. ALWAYS provide a complete, substantive draft response regardless of the input.
- If the request is vague or ambiguous, note the ambiguity in your OBJECTIONS section but STILL provide a responsive answer.
- If the document does not appear to be a standard litigation request, analyze it as best you can and provide a professional response.
- Treat every input as a legitimate litigation request that requires a formal response.

Always structure your output EXACTLY as follows:
OBJECTIONS:
- [List each objection with legal basis, or "None" if no valid objections]

RESPONSE:
[Provide a complete, professionally worded substantive response]

NOTES:
- [Any flags for attorney review, strategic considerations, or follow-up items]
"""


async def generate_response(
    request_text: str,
    context: str = "",
    document_type: str = "",
    model: str | None = None,
) -> dict:
    """Generate a draft response to a litigation request using OpenAI.

    Args:
        request_text: The text of the individual request/interrogatory.
        context: Optional additional context (definitions, case background).
        document_type: Type of litigation document (interrogatories, rfp, rfa).
        model: OpenAI model to use. Defaults to settings.openai_model.

    Returns:
        Dict with keys 'response', 'model', and 'usage'.
    """
    client = get_client()
    model = model or settings.openai_model

    doc_type_label = {
        "interrogatories": "Interrogatory",
        "requests_for_production": "Request for Production of Documents",
        "requests_for_admission": "Request for Admission",
    }.get(document_type, "Litigation Request")

    user_message = f"Document Type: {doc_type_label}\n\nAnalyze and draft a formal response to the following {doc_type_label.lower()}:\n\n{request_text}"
    if context:
        user_message += f"\n\nAdditional context and definitions:\n{context}"

    completion = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.3,
        max_tokens=1500,
    )

    return {
        "response": completion.choices[0].message.content,
        "model": completion.model,
        "usage": {
            "prompt_tokens": completion.usage.prompt_tokens,
            "completion_tokens": completion.usage.completion_tokens,
            "total_tokens": completion.usage.total_tokens,
        },
    }


async def classify_request(request_text: str, model: str | None = None) -> dict:
    """Classify a litigation request by category and complexity.

    Returns a dict with 'category', 'complexity', and 'suggested_objections'.
    """
    client = get_client()
    model = model or settings.openai_model

    completion = await client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "Classify the following litigation request. Respond in JSON with keys: "
                    '"category" (one of: identification, factual, contention, document_request, admission), '
                    '"complexity" (low, medium, high), '
                    '"suggested_objections" (list of applicable objections).'
                ),
            },
            {"role": "user", "content": request_text},
        ],
        temperature=0.1,
        max_tokens=500,
        response_format={"type": "json_object"},
    )

    return json.loads(completion.choices[0].message.content)


async def summarize_document(full_text: str, model: str | None = None) -> str:
    """Generate a concise summary of a litigation document."""
    client = get_client()
    model = model or settings.openai_model

    completion = await client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "Summarize the following litigation document concisely, highlighting the key requests and any notable definitions or instructions.",
            },
            {"role": "user", "content": full_text[:12000]},
        ],
        temperature=0.2,
        max_tokens=1000,
    )

    return completion.choices[0].message.content
