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
98+ Passing Tests
```

---

# Current Status

### Completed

- Multi-format document ingestion
- PDF parsing
- DOCX parsing
- OCR-based image text extraction
- Chunking pipeline
- Semantic embeddings
- Qdrant vector storage
- Retrieval pipeline
- LLM answer generation
- Verification layer
- Source citations
- Confidence scoring
- Dockerized deployment
- End-to-end API workflows

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