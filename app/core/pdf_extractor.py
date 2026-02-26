"""PDF text extraction using multiple backends for robust parsing."""

from pathlib import Path

import fitz  # PyMuPDF
import pdfplumber


def extract_with_pdfplumber(pdf_path: str) -> list[dict]:
    """Extract text and tables from a PDF using pdfplumber.

    Returns a list of dicts, one per page, with keys 'page', 'text', and 'tables'.
    """
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            tables = page.extract_tables() or []
            pages.append({"page": i, "text": text, "tables": tables})
    return pages


def extract_with_pymupdf(pdf_path: str) -> list[dict]:
    """Extract text from a PDF using PyMuPDF (fitz).

    Returns a list of dicts, one per page, with keys 'page' and 'text'.
    """
    pages = []
    doc = fitz.open(pdf_path)
    for i, page in enumerate(doc, start=1):
        text = page.get_text()
        pages.append({"page": i, "text": text})
    doc.close()
    return pages


def extract_text(pdf_path: str, method: str = "pdfplumber") -> list[dict]:
    """Extract text from a PDF file using the specified method.

    Args:
        pdf_path: Path to the PDF file.
        method: Extraction backend — 'pdfplumber' or 'pymupdf'.

    Raises:
        FileNotFoundError: If the PDF file does not exist.
        ValueError: If an unsupported method is specified.
    """
    if not Path(pdf_path).is_file():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    extractors = {
        "pdfplumber": extract_with_pdfplumber,
        "pymupdf": extract_with_pymupdf,
    }
    if method not in extractors:
        raise ValueError(f"Unsupported method '{method}'. Use one of: {list(extractors)}")

    return extractors[method](pdf_path)


def extract_full_text(pdf_path: str, method: str = "pdfplumber") -> str:
    """Convenience wrapper that returns the full document text as a single string."""
    pages = extract_text(pdf_path, method=method)
    return "\n\n".join(p["text"] for p in pages if p["text"])
