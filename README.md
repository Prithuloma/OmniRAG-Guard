# OmniRAG-Guard

> A Verification-Aware Retrieval-Augmented Generation (RAG) System with Evidence Grounding, Confidence Scoring, Source Citations, and Multi-Modal Document Support.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)
![Qdrant](https://img.shields.io/badge/Qdrant-Vector%20DB-orange)
![Docker](https://img.shields.io/badge/Docker-Containerized-blue)
![Tests](https://img.shields.io/badge/Tests-98%2B%20Passing-success)

---

## Overview

OmniRAG-Guard is an end-to-end Retrieval-Augmented Generation (RAG) platform designed to answer user questions from uploaded documents while providing evidence-based verification, confidence scoring, and source citations.

Unlike traditional RAG systems that simply retrieve information and generate responses, OmniRAG-Guard introduces a verification layer that evaluates how well generated answers are supported by retrieved evidence.

The system supports multiple document formats, semantic search using vector embeddings, grounded answer generation, and confidence-aware response validation.

---

## Key Features

### Multi-Format Document Support

- PDF
- DOCX
- TXT
- PNG
- JPG

### Automated Ingestion Pipeline

- Document Validation
- Text Extraction
- OCR Processing
- Chunking
- Embedding Generation
- Vector Storage

### Retrieval-Augmented Generation

- Semantic Search
- Context Retrieval
- LLM-Based Answer Generation

### Verification Layer

- Evidence Scoring
- Grounding Validation
- Confidence Calibration
- Source Attribution

### Infrastructure

- FastAPI Backend
- Qdrant Vector Database
- Dockerized Deployment
- Comprehensive Test Coverage

---

# System Architecture

```text
User Upload
     │
     ▼
 Document Parsing
     │
     ▼
 Text Chunking
     │
     ▼
 Embedding Generation
     │
     ▼
 Qdrant Vector Store

─────────────────────────────────

 User Query
     │
     ▼
 Retrieval Service
     │
     ▼
 LLM Generation
     │
     ▼
 Verification Layer
     │
     ▼
 Response + Citations + Confidence
```

---

## Core Components

| Layer | Technology |
|---------|------------|
| API Framework | FastAPI |
| Validation | Pydantic |
| Vector Database | Qdrant |
| PDF Parsing | PyMuPDF |
| DOCX Parsing | python-docx |
| OCR | pytesseract |
| Embeddings | Sentence Transformers |
| Testing | pytest |
| Containerization | Docker |

---

## Ingestion Pipeline

When a document is uploaded, it passes through a multi-stage ingestion workflow:

```text
Upload Document
        ↓
File Validation
        ↓
Parser Dispatcher
        ↓
PDF / DOCX / TXT / Image Parsing
        ↓
Text Chunking
        ↓
Embedding Generation
        ↓
Qdrant Vector Storage
```

### Supported Parsers

| Format | Parser |
|----------|----------|
| PDF | PyMuPDF |
| DOCX | python-docx |
| TXT | UTF-8 Text Parser |
| PNG/JPG | pytesseract OCR |

---

## Retrieval & Verification Pipeline

When a user submits a query:

```text
User Query
        ↓
Retrieval Service
        ↓
Qdrant Semantic Search
        ↓
Retrieved Chunks
        ↓
LLM Generation
        ↓
Verification Layer
        ↓
Response
```

### Verification Steps

- Lexical overlap analysis
- Semantic similarity scoring
- Grounding validation
- Confidence calculation
- Citation mapping

---

## End-to-End Workflow

### Document Ingestion

```text
Upload
 ↓
Validate
 ↓
Parse
 ↓
Chunk
 ↓
Embed
 ↓
Store in Qdrant
```

### Question Answering

```text
Query
 ↓
Retrieve
 ↓
Generate Answer
 ↓
Verify Grounding
 ↓
Attach Citations
 ↓
Return Response
```

---

## Project Structure

```text
backend/
│
├── app/
│   ├── api/
│   ├── core/
│   ├── models/
│   │
│   └── services/
│       ├── ingestion/
│       ├── embeddings/
│       ├── retrieval/
│       ├── verification/
│       ├── orchestration/
│       ├── llm/
│       └── vectorstore/
│
├── storage/
├── tests/
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

# API Endpoints

## Health Check

```http
GET /health
```

Example Response:

```json
{
  "status": "healthy"
}
```

---

## Upload Document

```http
POST /v1/upload
```

Supported Formats:

```text
PDF
DOCX
TXT
PNG
JPG
```

Example Response:

```json
{
  "document_id": "doc_123",
  "status": "success",
  "chunks_created": 18,
  "vectors_stored": 18
}
```

---

## Query Documents

```http
POST /v1/query
```

Example Request:

```json
{
  "query": "What is this document about?"
}
```

Example Response:

```json
{
  "answer": "The document describes a mock election event conducted to educate students about democratic voting procedures.",
  "confidence": 0.87,
  "grounded": true,
  "evidence_score": 0.82,
  "citations": [
    {
      "document_id": "doc_123",
      "chunk_id": "chunk_4"
    }
  ]
}
```

---

# Getting Started

## Clone Repository

```bash
git clone https://github.com/<your-username>/OmniRAG-Guard.git
cd OmniRAG-Guard
```

---

## Configuration & LLM Setup

OmniRAG-Guard supports both a simulated LLM (`MockLLM`) for development and testing, and a real **Google Gemini** integration.

### Settings Configuration

Configuration variables are stored in the `.env` file at the root of the project.

| Variable | Type | Default | Description |
|---|---|---|---|
| `LLM_PROVIDER` | `str` | `"mock"` | The active language model provider (`"mock"` or `"gemini"`). |
| `GEMINI_API_KEY` | `str` | `None` | Your Google Gemini API Key. |
| `GEMINI_MODEL` | `str` | `"gemini-1.5-flash"` | The Gemini model name to use for text generation. |

### How to obtain a Google Gemini API Key:
1. Navigate to [Google AI Studio](https://aistudio.google.com/).
2. Sign in with your Google account.
3. Click on the **Create API key** button.
4. Copy the generated key and set it in your environment or add it to the `.env` file:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   LLM_PROVIDER=gemini
   ```

### Fallback Mechanics & Prompt Injection Isolation
- **Dynamic Configuration Validation**: If `LLM_PROVIDER` is set to `"gemini"` but `GEMINI_API_KEY` is missing at start time, the system will log a warning and fallback to `MockLLM` dynamically to keep the system operational.
- **Query-Time Fallback**: If an active Gemini model call fails at runtime (e.g. quota limits, timeouts, invalid key), the request will catch the exception, dynamically resolve the answer using `MockLLM`, and append a warning to the response metadata (`fallback_warning`).
- **Prompt Injection Isolation**: Retrieved chunks are wrapped inside `<source_text>` XML tags to isolate document context from instructions, mitigating prompt injection risks.

---

## Run with Docker


```bash
docker compose up
```

---

## Open Swagger Documentation

```text
http://localhost:8000/docs
```

---

# Running Tests

Run all tests:

```bash
pytest
```

### Current Test Status

```text
101 Passing Tests (100% passing offline)
```

---

# Current Status

### Completed

- **Premium AI SaaS UI Overhaul**: Beautiful space-slate dark mode, custom scrollbars, and micro-animations mirroring Notion AI and Perplexity.
- **Conversational Chat Interface**: User and assistant message bubbles with automated scroll, multiline inputs (Enter/Shift+Enter), and visual RAG step progress tracking.
- **Google Gemini SDK Integration**: Added real `GeminiLLM` provider using strict retrieval-only grounding rules (answers only using retrieval context; rejects queries with the explicit fallback string when context is insufficient).
- **Dynamic Configuration & Runtime Fallback**: Automatic `MockLLM` fallback at startup if the API key is missing or at query-time if Gemini experiences errors (timeout, quota issues), adding warnings directly to response metadata.
- **Context Injection Prevention**: Wrapped retrieved source texts inside `<source_text>` XML tags.
- **Diagnostic Verification Panel**: Grounding indicators (Grounded/Partially Grounded/Low Evidence) with interactive citation highlights and keyword match markings.
- **Secure Authentication**: Credentials sign-in (email/password) and Google Sign-in with session persistent conversation history drawer.
- **Control Dashboard & History drawer**: Indicators for document size, chunk metrics, average latencies, knowledge base grids, pin/unpin options, and database purge actions.
- **SQLite Embedded Vector Database**: Integrated automatic local Sqlite-based vector database fallback when the Qdrant server is offline.
- **Multi-format Ingestion & OCR**: PDF, DOCX, TXT, and PNG/JPG OCR-based image text extraction.
- **Comprehensive Offline Mock Testing**: Fully simulated Gemini model responses, connection validation, and fallback mechanisms in python test cases.


---

# Team

## Prithuloma

Backend Development

- Ingestion Pipeline
- Retrieval Pipeline
- Embedding System
- Verification Layer
- Orchestration Layer
- Qdrant Integration
- API Development

## Revani

Frontend Development

- User Interface
- Upload Experience
- Query Experience
- Results Visualization
- Frontend Integration

---

# Future Work

- Advanced Semantic Verification
- Adaptive Retrieval Strategies
- Multi-Agent Orchestration
- Evidence Graph Construction
- Enhanced Hallucination Detection
- Research Paper Publication

---

# License

MIT License

---

## Acknowledgements

This project was developed as a collaborative effort to explore modern Retrieval-Augmented Generation (RAG) systems, verification-aware AI pipelines, and trustworthy document question-answering workflows.