"use client";

import { useState, useRef } from "react";
import { Upload, FileText, X } from "lucide-react";

interface UploadedFile {
  id: string;
  name: string;
  size: string;
}

export default function UploadPage() {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const addFiles = (fileList: FileList) => {
    const newFiles = Array.from(fileList).map((f) => ({
      id: Date.now() + f.name,
      name: f.name,
      size: (f.size / 1024).toFixed(1) + " KB",
    }));
    setFiles((prev) => [...prev, ...newFiles]);
  };

  const removeFile = (id: string) => setFiles((prev) => prev.filter((f) => f.id !== id));

  return (
    <div className="p-8">
      <h1 className="text-2xl font-semibold mb-1">Upload</h1>
      <p className="text-muted-foreground text-sm mb-8">Ingest documents into the RAG pipeline</p>

      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => { e.preventDefault(); setDragging(false); addFiles(e.dataTransfer.files); }}
        onClick={() => inputRef.current?.click()}
        style={{
          border: `2px dashed ${dragging ? "#6366f1" : "var(--border)"}`,
          borderRadius: "0.75rem",
          padding: "3rem",
          textAlign: "center",
          cursor: "pointer",
          marginBottom: "2rem",
          transition: "border-color 0.2s",
        }}
      >
        <input
          ref={inputRef}
          type="file"
          multiple
          accept=".pdf,.png,.jpg,.csv"
          style={{ display: "none" }}
          onChange={(e) => e.target.files && addFiles(e.target.files)}
        />
        <Upload className="w-8 h-8 text-muted-foreground mx-auto mb-3" />
        <p className="text-sm font-medium mb-1">Drop files here or click to browse</p>
        <p className="text-xs text-muted-foreground">Supports PDF, PNG, JPG, CSV</p>
      </div>

      {files.length > 0 && (
        <div className="rounded-lg border border-border bg-card p-4 space-y-2">
          <p className="text-sm font-medium mb-3">Queued files</p>
          {files.map((f) => (
            <div key={f.id} style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}
              className="rounded-md border border-border px-4 py-3">
              <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                <FileText className="w-4 h-4 text-muted-foreground" />
                <span className="text-sm">{f.name}</span>
                <span className="text-xs text-muted-foreground">{f.size}</span>
              </div>
              <button onClick={() => removeFile(f.id)}>
                <X className="w-4 h-4 text-muted-foreground hover:text-foreground" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}