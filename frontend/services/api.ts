const BASE_URL = "http://localhost:8000";

export async function checkHealth() {
  const res = await fetch(`${BASE_URL}/health`);
  if (!res.ok) {
    throw new Error(`Health check failed: ${res.status}`);
  }
  return res.json();
}

export async function queryRAG(query: string, topK = 3, filters?: any) {
  const res = await fetch(`${BASE_URL}/v1/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, top_k: topK, filters: filters || {} }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    const detail = errorData.detail;
    const message = 
      typeof detail === "string" 
        ? detail 
        : detail?.message || detail?.code || detail?.context?.detail || JSON.stringify(detail) || "Query failed";
    throw new Error(message);
  }
  return res.json();
}

export async function uploadFile(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${BASE_URL}/v1/upload/`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    const message = errorData.detail?.message || errorData.detail || "Upload failed";
    throw new Error(message);
  }
  return res.json();
}

export async function deleteFile(documentId: string) {
  const res = await fetch(`${BASE_URL}/v1/upload/${documentId}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    const message = errorData.detail?.message || errorData.detail || "Deletion failed";
    throw new Error(message);
  }
  return res.json();
}