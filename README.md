# OmniRAG-Guard

Adaptive Multi-Modal RAG with Hallucination Verification and Cost-Aware Model Routing

## Overview

OmniRAG-Guard is a production-grade multi-modal Retrieval-Augmented Generation (RAG) system designed to improve reliability, transparency, and efficiency in AI-generated responses.

The system retrieves and reasons over:
- PDFs
- Images
- Tables
- DOCX files
- Plain text

while reducing hallucinations through:
- Hybrid semantic and lexical verification,
- Source citation mapping,
- Calibrated confidence scoring,
- And adaptive retrieval filtering.

---

## Key Features

- **Multi-Modal Parsing**: High-fidelity text extraction for PDF, DOCX, TXT, PNG, JPG, JPEG documents using PyMuPDF, python-docx, and pytesseract OCR.
- **Provider-Backed Embeddings**: Configurable provider architecture supporting `sentence-transformers` (`all-MiniLM-L6-v2`) and local placeholders.
- **Scoped Document Retrieval**: Scopes vector queries to specific `document_ids`, `tags`, `filename`, or `upload_date`, with automatic fallback to global search.
- **Calibrated Confidence**: Confidence calibration blending retrieval similarity, grounding overlap, and chunk consensus.
- **Hybrid Groundedness Verification**: Fuses lexical token overlap and semantic embedding similarity to classify whether generated answers are supported by retrieved context.
- **Source Citation Mapping**: Automatically maps claims in the generated response back to specific parent documents, pages, and chunks.
- **One-Command Service Deployment**: Runs fully containerized backend services via Docker Compose.

---

## Architecture Diagram

```text
       [User Document Upload]
                 ↓
      [Ingestion Pipeline (API)]
                 ↓
    [Document Parser Dispatcher]
     ↙     ↓          ↓        ↘
  [PDF]  [DOCX]  [Plain Text] [Images (OCR)]
     ↘     ↓          ↓        ↗
      [Dynamic Text Chunking]
                 ↓
  [Embedding Service (MiniLM-L6)]
                 ↓
       [Qdrant Vector Store]
```

```text
       [User Query (API)]
                 ↓
  [Retrieval & Filtering (Qdrant)]
                 ↓
   [Context Assembly Engine]
                 ↓
     [LLM Generation Service]
                 ↓
  [Verification Service (Scoring)]
  - Grounding Blending
  - Citation Extraction
  - Confidence Calibration
                 ↓
     [Formatted Query Response]
```

---

## Tech Stack

- **Backend**: FastAPI, Pydantic, Uvicorn, Python 3.12+
- **AI/ML & Vector DB**: Qdrant, sentence-transformers (`all-MiniLM-L6-v2`)
- **Parsing & OCR**: PyMuPDF, python-docx, pytesseract (Tesseract OCR)
- **Deployment**: Docker, Docker Compose

---

## Repository Structure

```text
OmniRAG-Guard/
│
├── backend/
│   ├── app/
│   │   ├── api/          # Route controllers (health, upload, query)
│   │   ├── core/         # Global config and environment settings
│   │   ├── models/       # Pydantic request & response schemas
│   │   ├── services/     # Ingestion, retrieval, LLM, verification, orchestration
│   │   └── utils/        # General utilities
│   ├── tests/            # Test suite (98+ tests)
│   ├── Dockerfile
│   └── requirements.txt
│
├── docker-compose.yml    # Root orchestration compose
└── README.md
```

---

## Installation & Setup

### Local Setup
1. **Install Prerequisites**: Ensure you have Python 3.12+ and [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) installed on your host machine.
2. **Create Virtual Environment**:
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. **Install Dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
4. **Environment Variables**: Create a `.env` file in the `backend/` directory (see `.env.example` for reference).
5. **Run Application**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Containerized Setup (Docker Compose)
Launch the API and Qdrant DB in one command:
```bash
docker-compose up --build
```
* **API Documentation**: `http://localhost:8000/docs`
* **Qdrant DB Console**: `http://localhost:6333/dashboard`

---

## API Examples

### 1. Ingest Document (`POST /v1/upload/`)
* **Request**: Send a multipart form-data payload containing the file under `file`.
* **Response**:
  ```json
  {
    "document_id": "doc_a1b2c3d4e5f6",
    "status": "success",
    "chunks_created": 12,
    "vectors_stored": 12
  }
  ```

### 2. Query Pipeline (`POST /v1/query/`)
* **Request**:
  ```json
  {
    "query": "What was the revenue growth?",
    "top_k": 3,
    "filters": {
      "tags": ["finance"],
      "filename": "q3_report.pdf"
    }
  }
  ```
* **Response**:
  ```json
  {
    "success": true,
    "message": "Retrieved 1 chunk(s), generated an answer, and completed verification.",
    "timestamp": "2026-06-09T21:42:01Z",
    "query_id": "qry_f7e8d9c0b1a2",
    "query": "What was the revenue growth?",
    "status": "success",
    "retrieved_chunks": [
      {
        "chunk_id": "doc_a1b2c3d4e5f6:chunk:0",
        "document_id": "doc_a1b2c3d4e5f6",
        "page_number": 2,
        "text": "Revenue increased by 18% YoY in Q3.",
        "score": 0.91
      }
    ],
    "chunk_count": 1,
    "latency_ms": 420.5,
    "answer": "The revenue grew 18% year-over-year.",
    "confidence": 0.95,
    "evidence_score": 1.0,
    "grounding_score": 0.95,
    "citations": [
      {
        "document_id": "doc_a1b2c3d4e5f6",
        "chunk_id": "doc_a1b2c3d4e5f6:chunk:0",
        "page_number": 2
      }
    ],
    "retrieval_stats": {
      "chunks_retrieved": 1,
      "search_time_ms": 12.5,
      "rerank_time_ms": 0.0
    },
    "grounded": true,
    "verification_reason": "Answer is supported by retrieved chunks."
  }
  ```

---

## Test Coverage

The project maintains a rigorous, offline-safe test suite of 98 unit and integration tests. Run tests locally:
```bash
cd backend
python -m pytest
```

---

## Future Research Directions

1. **Graph-structured Verification**: Map contradiction matrices and logical contradictions using factual entity triple extraction.
2. **Dynamic Context-Length Routing**: Dynamically select LLM context assembly layout sizes based on query semantic density scores.
3. **Adaptive Agentic Retry**: Programmatically expand retrieval ranges (e.g. document-set widening) if the hallucination/groundedness score drops below acceptable levels.

---

## License

MIT License