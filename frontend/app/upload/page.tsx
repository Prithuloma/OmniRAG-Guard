"use client";

import { useState, useRef } from "react";
import { Upload, FileText, X, CheckCircle, Loader, Sparkles, Layers, ShieldCheck, ArrowRight, HardDrive } from "lucide-react";
import { uploadFile } from "@/services/api";
import { useAuth } from "@/context/AuthContext";
import { addHistory } from "@/lib/history";
import Link from "next/link";

interface UploadedFile {
  id: string;
  name: string;
  size: string;
  file: File;
  status: "queued" | "uploading" | "embedding" | "indexing" | "done" | "error";
  progress: number;
  docId?: string;
  chunksCreated?: number;
  vectorsStored?: number;
  pagesProcessed?: number;
}

export default function UploadPage() {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [isDragOver, setIsDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const { user } = useAuth();

  const addFiles = (fileList: FileList) => {
    const newFiles = Array.from(fileList).map((f) => ({
      id: (Date.now() + Math.random()).toString() + f.name,
      name: f.name,
      size: (f.size / 1024).toFixed(1) + " KB",
      file: f,
      status: "queued" as const,
      progress: 0,
    }));
    setFiles((prev) => [...prev, ...newFiles]);
  };

  const removeFile = (id: string) => setFiles((prev) => prev.filter((f) => f.id !== id));

  const runSimulatedProgress = (fileId: string, durationMs: number, onComplete: () => void) => {
    let currentProgress = 0;
    const interval = setInterval(() => {
      currentProgress += 5;
      setFiles((prev) =>
        prev.map((f) => (f.id === fileId ? { ...f, progress: Math.min(currentProgress, 99) } : f))
      );
      if (currentProgress >= 100) {
        clearInterval(interval);
        onComplete();
      }
    }, durationMs / 20);
  };

  const handleUpload = async () => {
    const queuedFiles = files.filter((f) => f.status === "queued");
    
    for (const f of queuedFiles) {
      // 1. Move to Uploading stage
      setFiles((prev) =>
        prev.map((x) => (x.id === f.id ? { ...x, status: "uploading", progress: 10 } : x))
      );

      try {
        // Run API Upload
        const responseData = await uploadFile(f.file);
        
        // 2. Move to Embedding generation stage (simulate for visual polish)
        setFiles((prev) =>
          prev.map((x) => (x.id === f.id ? { ...x, status: "embedding", progress: 45 } : x))
        );

        await new Promise((resolve) => setTimeout(resolve, 800));

        // 3. Move to Indexing stage
        setFiles((prev) =>
          prev.map((x) => (x.id === f.id ? { ...x, status: "indexing", progress: 80 } : x))
        );

        await new Promise((resolve) => setTimeout(resolve, 600));

        // 4. Complete
        setFiles((prev) =>
          prev.map((x) =>
            x.id === f.id
              ? {
                  ...x,
                  status: "done",
                  progress: 100,
                  docId: responseData.document_id,
                  chunksCreated: responseData.chunks_created,
                  vectorsStored: responseData.vectors_stored,
                  pagesProcessed: responseData.pages_processed,
                }
              : x
          )
        );

        const userId = user?.uid || "guest";
        if (responseData.document_id) {
          addHistory(userId, {
            documentId: responseData.document_id,
            filename: f.name,
            size: (f.file.size / 1024).toFixed(1) + " KB",
            chunks: responseData.chunks_created,
            pages: responseData.pages_processed,
          });
        }
      } catch (err: any) {
        console.error("Upload error details:", err);
        setFiles((prev) => prev.map((x) => (x.id === f.id ? { ...x, status: "error", progress: 0 } : x)));
      }
    }
  };

  const getStatusText = (f: UploadedFile) => {
    switch (f.status) {
      case "queued":
        return "Queued for ingestion";
      case "uploading":
        return `Uploading file... ${f.progress}%`;
      case "embedding":
        return "Generating dense vector embeddings...";
      case "indexing":
        return "Mapping chunks into Qdrant store...";
      case "done":
        return `Successfully indexed into ${f.chunksCreated ?? 0} chunks`;
      case "error":
        return "Ingestion failed. Invalid format or server timeout.";
      default:
        return "";
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "uploading":
        return "text-indigo-400";
      case "embedding":
        return "text-violet-400";
      case "indexing":
        return "text-amber-400 animate-pulse";
      case "done":
        return "text-emerald-400";
      case "error":
        return "text-red-400";
      default:
        return "text-muted-foreground/60";
    }
  };

  return (
    <div className="p-8 font-sans bg-slate-950 min-h-screen text-slate-100 space-y-8 animate-fade-in">
      <div className="border-b border-border/40 pb-5">
        <h1 className="text-lg font-bold text-slate-100">Ingest Knowledge Pool</h1>
        <p className="text-xs text-muted-foreground mt-0.5">
          Populate the RAG pipeline with corporate documents, guidelines, and PDF transcripts.
        </p>
      </div>

      {/* Drag & Drop Area */}
      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={(e) => { e.preventDefault(); setIsDragOver(false); addFiles(e.dataTransfer.files); }}
        onClick={() => inputRef.current?.click()}
        className={`border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all duration-300 relative group
          ${isDragOver 
            ? "border-primary bg-primary/5 shadow-inner" 
            : "border-border/80 bg-slate-900/10 hover:border-border hover:bg-slate-900/20"
          }`}
      >
        <input ref={inputRef} type="file" multiple accept=".pdf,.png,.jpg,.docx,.txt" style={{ display: "none" }}
          onChange={(e) => e.target.files && addFiles(e.target.files)} />
        <div className="p-3 bg-slate-900 border border-border/60 rounded-2xl inline-flex mb-4 text-muted-foreground group-hover:text-primary group-hover:border-primary/40 group-hover:scale-105 transition-all duration-300 shadow">
          <Upload className="w-6 h-6" />
        </div>
        <p className="text-xs font-semibold mb-1 text-slate-200">Drop files here or click to browse</p>
        <p className="text-[10px] text-muted-foreground/60">Supports PDF, DOCX, TXT, PNG, JPG files</p>
      </div>

      {files.length > 0 && (
        <div className="rounded-2xl border border-border/80 bg-slate-900/20 p-5 space-y-5 shadow-sm">
          <div className="flex justify-between items-center border-b border-border/40 pb-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">Selected Source Files</h3>
            <span className="text-[10px] bg-slate-950 px-2 py-0.5 border border-border rounded-full text-muted-foreground">
              {files.length} files
            </span>
          </div>

          {/* Files List */}
          <div className="space-y-3.5">
            {files.map((f) => {
              const showActions = f.status === "queued";
              const showProgress = f.status !== "queued" && f.status !== "done" && f.status !== "error";
              
              return (
                <div key={f.id} className="rounded-xl border border-border/70 p-4 bg-slate-900/35 flex flex-col gap-3 relative overflow-hidden transition-all hover:bg-slate-900/50">
                  {/* Status glow indicators */}
                  {f.status === "done" && (
                    <div className="absolute left-0 top-0 bottom-0 w-1 bg-emerald-500" />
                  )}

                  <div className="flex items-center justify-between gap-4">
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="p-2 rounded-lg bg-slate-950 border border-border/70 text-muted-foreground">
                        <FileText className="w-4 h-4 text-primary" />
                      </div>
                      <div className="min-w-0">
                        <span className="text-xs font-semibold text-slate-200 block truncate leading-snug">
                          {f.name}
                        </span>
                        <span className="text-[9px] text-muted-foreground/60 block mt-0.5 font-mono">
                          {f.size}
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center gap-2.5">
                      {f.status === "done" && (
                        <div className="flex items-center gap-1.5">
                          <span className="text-[10px] text-emerald-400 bg-emerald-500/5 border border-emerald-500/25 rounded-lg px-2 py-0.5 font-bold uppercase tracking-wide flex items-center gap-1">
                            <ShieldCheck className="w-3 h-3 text-emerald-400" />
                            Indexed
                          </span>
                          <Link
                            href="/chat"
                            className="p-1.5 rounded-lg bg-primary hover:opacity-95 text-primary-foreground transition-all cursor-pointer"
                            title="Query this document"
                          >
                            <ArrowRight className="w-3.5 h-3.5" />
                          </Link>
                        </div>
                      )}

                      {f.status === "error" && (
                        <span className="text-[9px] text-red-400 bg-red-500/5 border border-red-500/25 rounded-lg px-2.5 py-0.5 font-bold uppercase">
                          Failed
                        </span>
                      )}

                      {showProgress && (
                        <Loader className="w-4 h-4 animate-spin text-primary" />
                      )}

                      {showActions && (
                        <button
                          onClick={() => removeFile(f.id)}
                          className="p-1 rounded-lg hover:bg-slate-800 text-muted-foreground hover:text-white transition-colors cursor-pointer"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Description of Ingestion Pipeline Status */}
                  <div className="flex flex-col gap-1.5 mt-0.5">
                    <div className="flex justify-between items-center text-[10px]">
                      <span className={`font-semibold ${getStatusColor(f.status)}`}>
                        {getStatusText(f)}
                      </span>
                      {showProgress && (
                        <span className="font-mono text-muted-foreground">{f.progress}%</span>
                      )}
                    </div>

                    {/* Progress Bar */}
                    {showProgress && (
                      <div className="h-1.5 rounded-full bg-slate-950 overflow-hidden">
                        <div
                          className="h-full bg-primary rounded-full transition-all duration-300"
                          style={{ width: `${f.progress}%` }}
                        />
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          <div className="flex justify-end pt-3 border-t border-border/40">
            <button
              onClick={handleUpload}
              disabled={files.every((f) => f.status !== "queued")}
              className="inline-flex items-center gap-2 bg-primary text-primary-foreground px-5 py-3 rounded-xl text-xs font-semibold shadow-lg shadow-primary/10 hover:opacity-95 disabled:opacity-50 disabled:pointer-events-none transition-all cursor-pointer"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Index in RAG pipeline</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}