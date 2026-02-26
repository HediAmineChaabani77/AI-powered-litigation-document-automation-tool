"""Tests for the PDF extractor module."""

import pytest

from app.core.pdf_extractor import extract_text


def test_extract_text_file_not_found():
    with pytest.raises(FileNotFoundError):
        extract_text("/nonexistent/file.pdf")


def test_extract_text_invalid_method():
    # Create a temp file so FileNotFoundError isn't raised first
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
        with pytest.raises(ValueError, match="Unsupported method"):
            extract_text(f.name, method="invalid")
