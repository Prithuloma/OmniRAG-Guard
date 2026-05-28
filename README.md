# OmniRAG-Guard

Adaptive Multi-Modal RAG with Hallucination Verification and Cost-Aware Model Routing

## Overview

OmniRAG-Guard is a production-grade multi-modal Retrieval-Augmented Generation (RAG) system designed to improve reliability, transparency, and efficiency in AI-generated responses.

The system retrieves and reasons over:
- PDFs
- images
- tables
- charts
- documents

while reducing hallucinations through:
- semantic evidence verification,
- contradiction detection,
- confidence scoring,
- and adaptive retrieval retrying.

Additionally, the system dynamically routes queries between smaller and larger models based on query complexity to optimize inference cost and performance.

---

# Key Features

- Multi-modal document ingestion
- Advanced RAG pipeline
- Hallucination verification engine
- Semantic evidence checking
- Confidence-aware answer generation
- Adaptive retrieval retrying
- Cost-aware model routing
- Multi-agent orchestration
- Interactive AI dashboard

---

# Architecture

```text
User Query
    ↓
Router Agent
    ↓
Retrieval Agent
    ↓
Context Assembly
    ↓
LLM Generation
    ↓
Verification Agent
    ↓
Critic Agent
    ↓
Final Grounded Response
```

---

# Tech Stack

## Frontend
- Next.js
- TailwindCSS
- shadcn/ui

## Backend
- FastAPI
- Pydantic

## AI/ML
- LangGraph
- sentence-transformers
- BGE-small embeddings

## Vector Database
- Qdrant

## Parsing & OCR
- PyMuPDF
- Unstructured
- PaddleOCR

---

# Repository Structure

```text
OmniRAG-Guard/
│
├── frontend/
├── backend/
├── ingestion/
├── retrieval/
├── verification/
├── orchestration/
├── docs/
├── tests/
└── scripts/
```

---

# Current Development Status

## Completed
- repository setup
- backend foundation
- FastAPI initialization
- centralized config system
- API contract planning
- route skeletons

## In Progress
- upload pipeline
- local file storage
- frontend dashboard setup

---

# Team

## Prithu
- backend
- retrieval
- orchestration
- vector DB
- ingestion pipeline

## Revani
- frontend
- dashboard
- visualization
- UX integration

---

# Future Goals

- Cross-modal evidence validation
- Reliability scoring graph
- Retrieval retry orchestration
- Real-time monitoring dashboard
- Advanced hallucination tracing

---

# Setup (Coming Soon)

Setup instructions will be added as development progresses.

---

# License

MIT License