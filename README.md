# Litigation AI Tool

AI-powered litigation document analysis and response generation tool built with **Python**, **OpenAI API**, and **FastAPI**.

## Features

- **PDF Text Extraction** — Dual-backend support using PDFPlumber and PyMuPDF for robust text extraction from litigation documents
- **Document Parsing** — Automatic detection and structured parsing of interrogatories, requests for production (RFPs), and requests for admission (RFAs)
- **AI-Powered Response Generation** — Uses OpenAI GPT-4o to generate draft responses with objections and attorney review flags
- **Request Classification** — Automatically categorizes requests by type and complexity
- **Document Summarization** — Generates concise summaries of uploaded documents
- **REST API** — Full-featured FastAPI backend with interactive Swagger documentation
- **Web Interface** — Clean, responsive UI for uploading documents and reviewing AI-generated responses

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.11+ |
| AI / LLM | OpenAI API (GPT-4o / GPT-4 / GPT-5) |
| PDF Parsing | PDFPlumber, PyMuPDF (fitz) |
| Web Framework | FastAPI + Uvicorn |
| Frontend | HTML, CSS, vanilla JavaScript |
| Testing | pytest |

## Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/litigation-ai-tool.git
cd litigation-ai-tool

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your OpenAI API key

# Run the server
uvicorn app.main:app --reload

# Open http://localhost:8000 in your browser
# API docs at http://localhost:8000/docs
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/upload` | Upload a PDF document for analysis |
| `GET` | `/api/v1/documents/{id}/requests` | Get parsed requests from a document |
| `GET` | `/api/v1/documents/{id}/pages` | Get page-by-page extracted text |
| `POST` | `/api/v1/analyze` | Analyze a single request text |
| `POST` | `/api/v1/analyze/{id}` | Generate responses for all requests in a document |

## Project Structure

```
litigation-ai-tool/
├── app/
│   ├── api/
│   │   └── routes.py          # REST API endpoints
│   ├── core/
│   │   ├── pdf_extractor.py   # PDF text extraction (PDFPlumber + PyMuPDF)
│   │   └── document_parser.py # Litigation document parsing & structuring
│   ├── services/
│   │   └── openai_client.py   # OpenAI API integration
│   ├── static/css/
│   │   └── style.css
│   ├── templates/
│   │   └── index.html         # Web interface
│   ├── config.py              # App configuration
│   └── main.py                # FastAPI app entry point
├── tests/
│   ├── test_api.py
│   ├── test_document_parser.py
│   └── test_pdf_extractor.py
├── requirements.txt
├── .env.example
└── README.md
```

## Running Tests

```bash
pytest tests/ -v
```

## License

MIT
