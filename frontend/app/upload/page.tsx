"use client";

import { useState, useRef } from "react";
import { Upload, FileText, X, CheckCircle, Loader } from "lucide-react";
import { uploadFile } from "@/services/api";
import { useAuth } from "@/context/AuthContext";
import { addHistory } from "@/lib/history";

interface UploadedFile {
  id: string;
  name: string;
  size: string;
  file: File;
  status: "queued" | "uploading" | "done" | "error";
  docId?: string;
}

export default function UploadPage() {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);
  const { user } = useAuth();

  const addFiles = (fileList: FileList) => {
    const newFiles = Array.from(fileList).map((f) => ({
      id: Date.now() + f.name,
      name: f.name,
      size: (f.size / 1024).toFixed(1) + " KB",
      file: f,
      status: "queued" as const,
    }));
    setFiles((prev) => [...prev, ...newFiles]);
  };

  const removeFile = (id: string) => setFiles((prev) => prev.filter((f) => f.id !== id));

  const handleUpload = async () => {
    for (const f of files.filter((f) => f.status === "queued")) {
      setFiles((prev) => prev.map((x) => x.id === f.id ? { ...x, status: "uploading" } : x));
      try {
        const data = await uploadFile(f.file);
        setFiles((prev) => prev.map((x) => x.id === f.id ? { ...x, status: "done", docId: data.document_id } : x));
        if (user && data.document_id) {
          addHistory(user.uid, {
            documentId: data.document_id,
            filename: f.name,
            size: (f.file.size / 1024).toFixed(1) + " KB",
          });
        }
      } catch {
        setFiles((prev) => prev.map((x) => x.id === f.id ? { ...x, status: "error" } : x));
      }
    }
  };

  const statusIcon = (status: string) => {
    if (status === "uploading") return <Loader className="w-4 h-4 animate-spin text-yellow-400" />;
    if (status === "done") return <CheckCircle className="w-4 h-4 text-green-400" />;
    if (status === "error") return <X className="w-4 h-4 text-red-400" />;
    return null;
  };

  return (
    <div className="p-8">
      <h1 className="text-2xl font-semibold mb-1">Upload</h1>
      <p className="text-muted-foreground text-sm mb-8">Ingest documents into the RAG pipeline</p>

      <div
        onDragOver={(e) => { e.preventDefault(); }}
        onDrop={(e) => { e.preventDefault(); addFiles(e.dataTransfer.files); }}
        onClick={() => inputRef.current?.click()}
        style={{
          border: "2px dashed var(--border)",
          borderRadius: "0.75rem",
          padding: "3rem",
          textAlign: "center",
          cursor: "pointer",
          marginBottom: "2rem",
        }}
      >
        <input ref={inputRef} type="file" multiple accept=".pdf,.png,.jpg,.docx,.txt" style={{ display: "none" }}
          onChange={(e) => e.target.files && addFiles(e.target.files)} />
        <Upload className="w-8 h-8 text-muted-foreground mx-auto mb-3" />
        <p className="text-sm font-medium mb-1">Drop files here or click to browse</p>
        <p className="text-xs text-muted-foreground">Supports PDF, DOCX, TXT, PNG, JPG</p>
      </div>

      {files.length > 0 && (
        <div className="rounded-lg border border-border bg-card p-4">
          <p className="text-sm font-medium mb-3">Files</p>
          <div style={{ display: "flex", flexDirection: "column", gap: "8px", marginBottom: "16px" }}>
            {files.map((f) => (
              <div key={f.id} style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}
                className="rounded-md border border-border px-4 py-3">
                <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                  <FileText className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm">{f.name}</span>
                  <span className="text-xs text-muted-foreground">{f.size}</span>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  {statusIcon(f.status)}
                  {f.status === "queued" && (
                    <button onClick={(e) => { e.stopPropagation(); removeFile(f.id); }}>
                      <X className="w-4 h-4 text-muted-foreground" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
          <button
            onClick={handleUpload}
            className="rounded-lg bg-primary text-primary-foreground px-4 py-2 text-sm font-medium hover:opacity-90 transition-opacity"
          >
            Upload to RAG pipeline
          </button>
        </div>
      )}
    </div>
  );
}