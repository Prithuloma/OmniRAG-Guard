const BASE_URL = "http://localhost:8000";

export async function checkHealth() {
  const res = await fetch(`${BASE_URL}/health`);
  return res.json();
}

export async function queryRAG(query: string, topK = 3) {
  const res = await fetch(`${BASE_URL}/v1/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, top_k: topK }),
  });
  return res.json();
}

export async function uploadFile(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${BASE_URL}/v1/upload/`, {
    method: "POST",
    body: formData,
  });
  return res.json();
}