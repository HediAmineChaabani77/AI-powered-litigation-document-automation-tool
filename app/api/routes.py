"""REST API routes for the litigation AI tool."""

import asyncio
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from openai import AuthenticationError, APIConnectionError, RateLimitError
from pydantic import BaseModel

from app.config import settings
from app.core.document_parser import parse_document
from app.core.pdf_extractor import extract_full_text, extract_text
from app.services.openai_client import (
    classify_request,
    generate_response,
    summarize_document,
)

router = APIRouter(prefix="/api/v1", tags=["litigation"])

UPLOAD_DIR = Path(settings.upload_dir)
UPLOAD_DIR.mkdir(exist_ok=True)


class AnalyzeRequest(BaseModel):
    request_text: str
    context: str = ""
    document_type: str = ""
    model: str | None = None


class AnalyzeResponse(BaseModel):
    response: str
    model: str
    usage: dict


class DocumentSummary(BaseModel):
    document_id: str
    title: str
    document_type: str
    num_requests: int
    summary: str
    requests: list[dict]


def _handle_openai_error(exc: Exception):
    """Convert OpenAI SDK exceptions to appropriate HTTP errors."""
    if isinstance(exc, AuthenticationError):
        raise HTTPException(status_code=502, detail="OpenAI API key is invalid. Check your OPENAI_API_KEY environment variable.")
    if isinstance(exc, RateLimitError):
        raise HTTPException(status_code=429, detail="OpenAI rate limit reached. Please try again shortly.")
    if isinstance(exc, APIConnectionError):
        raise HTTPException(status_code=502, detail="Could not connect to OpenAI API.")
    raise HTTPException(status_code=500, detail=f"OpenAI error: {exc}")


@router.post("/upload", response_model=DocumentSummary)
async def upload_document(file: UploadFile = File(...)):
    """Upload a PDF litigation document for analysis."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    doc_id = str(uuid.uuid4())
    save_path = UPLOAD_DIR / f"{doc_id}.pdf"

    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    full_text = extract_full_text(str(save_path))
    parsed = parse_document(full_text, title=file.filename)

    try:
        summary = await summarize_document(full_text)
    except (AuthenticationError, APIConnectionError, RateLimitError) as exc:
        _handle_openai_error(exc)

    return DocumentSummary(
        document_id=doc_id,
        title=parsed.title,
        document_type=parsed.document_type,
        num_requests=len(parsed.requests),
        summary=summary,
        requests=[
            {"number": r.number, "text": r.text, "definitions_referenced": r.definitions_referenced}
            for r in parsed.requests
        ],
    )


@router.get("/documents/{document_id}/requests")
async def get_requests(document_id: str):
    """Get all parsed requests from a previously uploaded document."""
    pdf_path = UPLOAD_DIR / f"{document_id}.pdf"
    if not pdf_path.is_file():
        raise HTTPException(status_code=404, detail="Document not found.")

    full_text = extract_full_text(str(pdf_path))
    parsed = parse_document(full_text)

    return {
        "document_id": document_id,
        "document_type": parsed.document_type,
        "requests": [
            {"number": r.number, "text": r.text, "definitions_referenced": r.definitions_referenced}
            for r in parsed.requests
        ],
    }


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_request(body: AnalyzeRequest):
    """Generate an AI-drafted response to a single litigation request."""
    try:
        result = await generate_response(
            request_text=body.request_text,
            context=body.context,
            document_type=body.document_type,
            model=body.model,
        )
    except (AuthenticationError, APIConnectionError, RateLimitError) as exc:
        _handle_openai_error(exc)
    return AnalyzeResponse(**result)


class AnalyzeAllRequest(BaseModel):
    document_type: str = ""


@router.post("/analyze/{document_id}")
async def analyze_all_requests(document_id: str, body: AnalyzeAllRequest | None = None):
    """Analyze all requests in a document and generate draft responses."""
    pdf_path = UPLOAD_DIR / f"{document_id}.pdf"
    if not pdf_path.is_file():
        raise HTTPException(status_code=404, detail="Document not found.")

    full_text = extract_full_text(str(pdf_path))
    parsed = parse_document(full_text)

    doc_type = (body.document_type if body and body.document_type else parsed.document_type)

    definitions_context = ""
    if parsed.definitions:
        definitions_context = "Defined terms:\n" + "\n".join(
            f'- "{term}": {defn}' for term, defn in parsed.definitions.items()
        )

    try:
        tasks = [
            asyncio.gather(
                classify_request(req.text),
                generate_response(req.text, context=definitions_context, document_type=doc_type),
            )
            for req in parsed.requests
        ]
        pairs = await asyncio.gather(*tasks)
    except (AuthenticationError, APIConnectionError, RateLimitError) as exc:
        _handle_openai_error(exc)

    results = []
    for req, (classification, response) in zip(parsed.requests, pairs):
        results.append({
            "request_number": req.number,
            "request_text": req.text,
            "classification": classification,
            "draft_response": response["response"],
            "model": response["model"],
            "usage": response["usage"],
        })

    return {"document_id": document_id, "results": results}


@router.get("/documents/{document_id}/pages")
async def get_pages(document_id: str, method: str = "pdfplumber"):
    """Get page-by-page extracted text from a document."""
    pdf_path = UPLOAD_DIR / f"{document_id}.pdf"
    if not pdf_path.is_file():
        raise HTTPException(status_code=404, detail="Document not found.")

    pages = extract_text(str(pdf_path), method=method)
    return {"document_id": document_id, "method": method, "pages": pages}
