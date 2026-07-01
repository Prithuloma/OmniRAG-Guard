# OmniRAG-Guard — System Architecture & Flows

This document outlines the core system architecture, pipeline layers, and data processing paths of OmniRAG-Guard.

---

## Architectural Diagram Overview

```text
    ┌──────────────────────────────────────────────┐
    │                   Frontend                   │
    └──────────────────────┬───────────────────────┘
                           │ API Requests
                           ▼
    ┌──────────────────────────────────────────────┐
    │                FastAPI Server                │
    └──────────────────────┬───────────────────────┘
                           │ Ingestion & Search Flows
                           ▼
```

### 1. Ingestion Pipeline (Upload Path)
When a file is uploaded, it runs through validation, parsing, chunking, embedding generation, and vector persistence:

```text
   Upload Document (multipart/form-data)
              │
              ▼
      [File Validator] (Validates format, MIME type, size limit)
              │
              ▼
     [Parser Dispatcher] (Selects parsing engine based on format)
      ├── PDFParser  (PyMuPDF / Page-by-page extraction)
      ├── DocxParser (python-docx / Paragraph & table extraction)
      ├── TextParser (Plain UTF-8 text decoder)
      └── ImageParser (pytesseract / OCR text extraction)
              │
              ▼
     [Text Chunker] (Splits text into size-controlled overlapping blocks)
              │
              ▼
  [Embedding Service] (Loads sentence-transformers / MiniLM-L6 embeddings)
              │
              ▼
    [Qdrant Store] (Upserts embeddings and metadata payloads)
```

---

### 2. Retrieval-Verification Pipeline (Query Path)
When a query is submitted, retrieval filtering is applied, context is gathered, LLM generates an answer, verification is run, and the calibrated result is returned:

```text
               Submit Query (JSON body)
                          │
                          ▼
                  [Retrieval Service]
                          │ Check scopes (document_ids, tags, filename)
                          ▼
            [Qdrant Semantic Search]
                          │ (Optional fallback to global search if 0 matches)
                          ▼
              [Retrieved Context Chunks]
                          │
                          ▼
               [LLM Generation Service]
                          │ (Generates answer grounded in retrieved chunks)
                          ▼
              [Groundedness Verification]
               ├── Lexical overlap check
               ├── Semantic embedding similarity check
               ├── Calibrated confidence calculation
               └── Citation mapping
                          │
                          ▼
        [API Response JSON (Citations + Confidence)]
```

---

## Key Pipelines Detail

### Ingestion Component
* **Parser Dispatcher**: Decouples formatting logic. Adding a new file type is as simple as subclassing `BaseParser` and registering it in [parser_dispatcher.py](file:///c:/projects/OmniRAG-Guard/backend/app/services/ingestion/parser_dispatcher.py).
* **Chunking**: Preserves structural coordinates (such as source pages, titles, filenames) inside metadata tags for downstream citation linking.

### RAG Component
* **Global Fallback**: Ensures system robustness. If a user filters by tag/document but those documents lack matching vocabulary, the engine retries globally to prevent blank answers.
* **Calibrated Verification**: Combines lexical coverage (token matches) and semantic vector distance between the output answer and the source texts to flag hallucinations and calculate true confidence.
