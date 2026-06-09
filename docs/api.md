# OmniRAG-Guard — API Integration Reference

This document provides the API contracts, request/response payloads, error structures, and implementation guidelines for frontend integration.

* **Base URL**: `http://localhost:8000`
* **Swagger OpenAPI Docs**: `http://localhost:8000/docs`
* **ReDoc Docs**: `http://localhost:8000/redoc`

---

## Endpoints Reference

### 1. Ingest Document

* **Path**: `POST /v1/upload/`
* **Content-Type**: `multipart/form-data`
* **Authentication**: None (current version)

#### Request Fields
* `file`: Binary file. Supported formats: `.pdf`, `.docx`, `.txt`, `.png`, `.jpg`, `.jpeg`.

#### Success Response (`200 OK`)
```json
{
  "document_id": "doc_a1b2c3d4e5f6",
  "status": "success",
  "chunks_created": 12,
  "vectors_stored": 12
}
```

#### Error Responses

##### validation_failed (`422 Unprocessable Entity`)
Returned if the file format is unsupported, too large, or fails structural validation.
```json
{
  "detail": {
    "code": "validation_failed",
    "message": "File extension '.exe' is not supported.",
    "detail": "Supported formats: PDF, DOCX, TXT, PNG, JPG, JPEG"
  }
}
```

##### ingestion_failed (`422 Unprocessable Entity`)
Returned if parsing, chunking, or indexing fails during pipeline execution.
```json
{
  "detail": {
    "code": "ingestion_failed",
    "message": "Document parsing failed.",
    "document_id": "doc_a1b2c3d4e5f6",
    "ingestion_status": "failed"
  }
}
```

##### file_save_failed (`500 Internal Server Error`)
Returned if local file persistence fails.
```json
{
  "detail": {
    "code": "file_save_failed",
    "message": "Failed to save uploaded file."
  }
}
```

---

### 2. Query Pipeline

* **Path**: `POST /v1/query`
* **Content-Type**: `application/json`

#### Request Schema
```json
{
  "query": "What were the key revenue drivers?",
  "top_k": 3,
  "filters": {
    "document_ids": ["doc_abc123"],
    "document_id": "doc_abc123",
    "tags": ["finance"],
    "filename": "q3_report.pdf",
    "upload_date": "2026-06-09"
  }
}
```
* Note: All fields inside the `filters` block are optional.

#### Success Response (`200 OK`)
```json
{
  "success": true,
  "message": "Retrieved 1 chunk(s), generated an answer, and completed verification.",
  "timestamp": "2026-06-09T21:42:01.000Z",
  "query_id": "qry_f7e8d9c0b1a2",
  "query": "What were the key revenue drivers?",
  "status": "success",
  "retrieved_chunks": [
    {
      "chunk_id": "doc_abc123:chunk:0",
      "document_id": "doc_abc123",
      "page_number": 2,
      "text": "SaaS subscriptions drove revenue growth in Q3.",
      "score": 0.91
    }
  ],
  "chunk_count": 1,
  "latency_ms": 142.5,
  "answer": "The primary revenue drivers were SaaS subscriptions.",
  "confidence": 0.95,
  "evidence_score": 1.0,
  "grounding_score": 0.95,
  "citations": [
    {
      "document_id": "doc_abc123",
      "chunk_id": "doc_abc123:chunk:0",
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

#### Error Responses

##### empty_query (`422 Unprocessable Entity`)
Returned if the query string is empty or contains only whitespace.
```json
{
  "detail": {
    "code": "empty_query",
    "message": "Query must not be empty.",
    "field": "query"
  }
}
```

##### retrieval_failed / qdrant_unavailable (`503 Service Unavailable`)
Returned if there is a problem communicating with the Qdrant vector database or generating query embeddings.
```json
{
  "detail": {
    "code": "qdrant_unavailable",
    "field": "query",
    "context": {
      "detail": "Failed to connect to vector database."
    }
  }
}
```

---

### 3. Health Check

* **Path**: `GET /health`
* **Content-Type**: `application/json`

#### Response (`200 OK` or `503 Service Unavailable`)
```json
{
  "status": "healthy",
  "services": {
    "api": "healthy",
    "qdrant": "healthy",
    "embeddings": "healthy"
  }
}
```

---

## Expected Frontend Behavior Guidelines

1. **Upload Form Handling**:
   * Use HTML `<input type="file" name="file" />` and POST with `multipart/form-data`.
   * Implement a loading indicator showing that the pipeline is executing parsing, chunking, and embedding generation.
2. **Confidence and Scores Visualization**:
   * Bind the `confidence` score (values from `0.0` to `1.0`) to a visual indicator (e.g. gauge or colored bar).
   * Render a warning badge or color shift (e.g. Yellow or Red) if `grounded` is `false` or if `confidence < 0.5`, indicating a potential hallucination risk.
3. **Citation Highlighting**:
   * Loop through `citations` to display small reference numbers or cards next to sentences (similar to academic search engines).
   * Matching citations to corresponding items in `retrieved_chunks` by comparing `chunk_id` allows users to click the citation and view the exact source text chunk and source document page.
4. **Error Resilience**:
   * Catch `503` codes on query and show a user-friendly message asking to wait or verify database connection state.
