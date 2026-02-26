"""OpenAI API integration for generating litigation responses."""

from openai import OpenAI

from app.config import settings

_client: OpenAI | None = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.openai_api_key.strip())
    return _client


SYSTEM_PROMPT = """You are a litigation support assistant. Your role is to:
1. Analyze legal requests (interrogatories, requests for production, requests for admission).
2. Generate clear, professionally worded draft responses.
3. Identify potential objections (relevance, overbreadth, privilege, etc.).
4. Flag requests that may need attorney review.

Always structure your output with:
- OBJECTIONS (if any)
- RESPONSE
- NOTES (flags for attorney review)
"""


def generate_response(
    request_text: str,
    context: str = "",
    model: str | None = None,
) -> dict:
    """Generate a draft response to a litigation request using OpenAI.

    Args:
        request_text: The text of the individual request/interrogatory.
        context: Optional additional context (definitions, case background).
        model: OpenAI model to use. Defaults to settings.openai_model.

    Returns:
        Dict with keys 'response', 'model', and 'usage'.
    """
    client = get_client()
    model = model or settings.openai_model

    user_message = f"Analyze and draft a response to the following litigation request:\n\n{request_text}"
    if context:
        user_message += f"\n\nAdditional context:\n{context}"

    completion = client.chat.completions.create(
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


def classify_request(request_text: str, model: str | None = None) -> dict:
    """Classify a litigation request by category and complexity.

    Returns a dict with 'category', 'complexity', and 'suggested_objections'.
    """
    client = get_client()
    model = model or settings.openai_model

    completion = client.chat.completions.create(
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

    import json

    return json.loads(completion.choices[0].message.content)


def summarize_document(full_text: str, model: str | None = None) -> str:
    """Generate a concise summary of a litigation document."""
    client = get_client()
    model = model or settings.openai_model

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "Summarize the following litigation document concisely, highlighting the key requests and any notable definitions or instructions.",
            },
            {"role": "user", "content": full_text[:12000]},  # Truncate to stay within limits
        ],
        temperature=0.2,
        max_tokens=1000,
    )

    return completion.choices[0].message.content
