"""Tests for the document parser module."""

from app.core.document_parser import (
    Request,
    detect_document_type,
    extract_definitions,
    extract_requests,
    parse_document,
)


def test_detect_interrogatories():
    assert detect_document_type("INTERROGATORY NO. 1") == "interrogatories"


def test_detect_rfp():
    assert detect_document_type("Request for Production of Documents") == "requests_for_production"


def test_detect_rfa():
    assert detect_document_type("Request for Admission") == "requests_for_admission"


def test_detect_unknown():
    assert detect_document_type("Some random legal text") == "unknown"


def test_extract_definitions():
    text = '"COMPANY" means Acme Corp and all subsidiaries. "DOCUMENTS" refers to any written material.'
    defs = extract_definitions(text)
    assert "COMPANY" in defs
    assert "Acme Corp" in defs["COMPANY"]
    assert "DOCUMENTS" in defs


def test_extract_requests_numbered():
    text = (
        "REQUEST NO. 1: Produce all communications regarding the contract. "
        "REQUEST NO. 2: Identify all persons with knowledge of the incident."
    )
    requests = extract_requests(text)
    assert len(requests) == 2
    assert requests[0].number == 1
    assert "communications" in requests[0].text


def test_parse_document_integration():
    text = (
        'INTERROGATORIES\n\n'
        '"DEFENDANT" means ABC Corp.\n\n'
        'INTERROGATORY NO. 1: State your full legal name. '
        'INTERROGATORY NO. 2: Identify the DEFENDANT\'s officers.'
    )
    doc = parse_document(text, title="Test Interrogatories")
    assert doc.document_type == "interrogatories"
    assert doc.title == "Test Interrogatories"
    assert len(doc.requests) == 2
