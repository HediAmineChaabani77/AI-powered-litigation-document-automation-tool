"""Parse and structure litigation documents (interrogatories, RFPs, RFAs)."""

import re
from dataclasses import dataclass, field


@dataclass
class Request:
    """A single request extracted from a litigation document."""

    number: int
    text: str
    category: str = ""
    definitions_referenced: list[str] = field(default_factory=list)


@dataclass
class ParsedDocument:
    """Structured representation of a parsed litigation document."""

    title: str
    document_type: str
    parties: dict[str, str] = field(default_factory=dict)
    definitions: dict[str, str] = field(default_factory=dict)
    instructions: list[str] = field(default_factory=list)
    requests: list[Request] = field(default_factory=list)
    raw_text: str = ""


# Patterns for common litigation request numbering
_REQUEST_PATTERNS = [
    re.compile(
        r"(?:REQUEST|INTERROGATORY|DEMAND)\s*(?:NO\.|#|NUMBER)?\s*(\d+)[:\.\s]+(.*?)(?=(?:REQUEST|INTERROGATORY|DEMAND)\s*(?:NO\.|#|NUMBER)?\s*\d+|$)",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"(\d+)\.\s+(.*?)(?=\d+\.\s+|$)",
        re.DOTALL,
    ),
]

_DEFINITION_PATTERN = re.compile(
    r'"([^"]+)"\s+(?:means|refers to|shall mean)\s+(.*?)(?="|$)',
    re.IGNORECASE | re.DOTALL,
)


def detect_document_type(text: str) -> str:
    """Detect the type of litigation document from its text."""
    text_lower = text.lower()
    type_keywords = {
        "interrogatory": "interrogatories",
        "request for production": "requests_for_production",
        "request for admission": "requests_for_admission",
        "rfp": "requests_for_production",
        "rfa": "requests_for_admission",
        "demand for inspection": "requests_for_production",
    }
    for keyword, doc_type in type_keywords.items():
        if keyword in text_lower:
            return doc_type
    return "unknown"


def extract_definitions(text: str) -> dict[str, str]:
    """Extract defined terms from the document."""
    definitions = {}
    for match in _DEFINITION_PATTERN.finditer(text):
        term = match.group(1).strip()
        definition = match.group(2).strip()
        definitions[term] = definition
    return definitions


def extract_requests(text: str) -> list[Request]:
    """Extract individual requests/interrogatories from the document text."""
    for pattern in _REQUEST_PATTERNS:
        matches = list(pattern.finditer(text))
        if matches:
            return [
                Request(number=int(m.group(1)), text=m.group(2).strip())
                for m in matches
            ]
    return []


def parse_document(text: str, title: str = "") -> ParsedDocument:
    """Parse raw document text into a structured ParsedDocument."""
    doc_type = detect_document_type(text)
    definitions = extract_definitions(text)
    requests = extract_requests(text)

    # Tag requests that reference defined terms
    for req in requests:
        for term in definitions:
            if term.lower() in req.text.lower():
                req.definitions_referenced.append(term)

    return ParsedDocument(
        title=title or "Untitled Document",
        document_type=doc_type,
        definitions=definitions,
        requests=requests,
        raw_text=text,
    )
