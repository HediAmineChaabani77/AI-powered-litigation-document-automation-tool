"""REST API routes for the litigation AI tool."""

import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
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
    summary = summarize_document(full_text)

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
    result = generate_response(
        request_text=body.request_text,
        context=body.context,
        model=body.model,
    )
    return AnalyzeResponse(**result)


@router.post("/analyze/{document_id}")
async def analyze_all_requests(document_id: str):
    """Analyze all requests in a document and generate draft responses."""
    pdf_path = UPLOAD_DIR / f"{document_id}.pdf"
    if not pdf_path.is_file():
        raise HTTPException(status_code=404, detail="Document not found.")

    full_text = extract_full_text(str(pdf_path))
    parsed = parse_document(full_text)

    definitions_context = ""
    if parsed.definitions:
        definitions_context = "Defined terms:\n" + "\n".join(
            f'- "{term}": {defn}' for term, defn in parsed.definitions.items()
        )

    results = []
    for req in parsed.requests:
        classification = classify_request(req.text)
        response = generate_response(req.text, context=definitions_context)
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
