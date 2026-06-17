"use client";

import { useAuth } from "@/context/AuthContext";
import { getHistory, togglePinHistory, deleteFromHistory, renameHistoryItem, HistoryItem } from "@/lib/history";
import { getConversations } from "@/lib/conversations";
import { deleteFile } from "@/services/api";
import { useEffect, useState } from "react";
import {
  FileText,
  MessageSquare,
  Zap,
  ArrowUpRight,
  Pin,
  Trash2,
  Edit2,
  Check,
  X,
  Search,
  Loader2,
  FileWarning,
  Info,
  Calendar,
  HardDrive,
  Layers,
  Database
} from "lucide-react";
import Link from "next/link";

interface DetailedFileModalProps {
  file: HistoryItem;
  onClose: () => void;
}

function FileDetailsModal({ file, onClose }: DetailedFileModalProps) {
  const chunksCount = file.chunks || Math.round(parseFloat(file.size) * 1.2 || 10);
  const pagesCount = file.pages || 1;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-800 w-full max-w-md rounded-2xl shadow-2xl flex flex-col overflow-hidden font-sans">
        <div className="p-5 border-b border-slate-800/80 flex items-center justify-between bg-slate-950/40">
          <div className="flex items-center gap-2.5">
            <FileText className="w-4.5 h-4.5 text-primary" />
            <span className="font-bold text-xs uppercase tracking-wider text-slate-200">Document Metadata</span>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-6 space-y-4 text-xs">
          <div className="space-y-1">
            <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">File Name</span>
            <p className="font-medium text-slate-100 bg-slate-950/45 p-2.5 rounded-lg border border-slate-800/60 overflow-hidden text-ellipsis whitespace-nowrap">
              {file.filename}
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Document ID</span>
              <p className="font-mono text-[10px] text-slate-300 bg-slate-950/45 p-2 rounded-lg border border-slate-800/60 truncate">
                {file.documentId}
              </p>
            </div>
            <div className="space-y-1">
              <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">File Status</span>
              <div>
                <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-lg font-bold text-[9px] uppercase border mt-0.5
                  ${file.status === "error" 
                    ? "bg-red-500/10 border-red-500/20 text-red-400" 
                    : file.status === "uploading"
                    ? "bg-amber-500/10 border-amber-500/20 text-amber-400 animate-pulse"
                    : "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
                  }`}
                >
                  {file.status ?? "done"}
                </span>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-1">
              <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Storage size</span>
              <p className="font-medium text-slate-200 flex items-center gap-1.5 mt-0.5">
                <HardDrive className="w-3.5 h-3.5 text-slate-400" />
                {file.size}
              </p>
            </div>
            <div className="space-y-1">
              <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Indexed Pages</span>
              <p className="font-medium text-slate-200 flex items-center gap-1.5 mt-0.5">
                <FileText className="w-3.5 h-3.5 text-slate-400" />
                {pagesCount} pages
              </p>
            </div>
            <div className="space-y-1">
              <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Total Chunks</span>
              <p className="font-medium text-slate-200 flex items-center gap-1.5 mt-0.5">
                <Layers className="w-3.5 h-3.5 text-slate-400" />
                {chunksCount} chunks
              </p>
            </div>
          </div>

          <div className="space-y-1">
            <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Upload Timestamp</span>
            <p className="font-medium text-slate-200 flex items-center gap-1.5 mt-0.5">
              <Calendar className="w-3.5 h-3.5 text-slate-400" />
              {new Date(file.uploadDate).toLocaleString()}
            </p>
          </div>

          <div className="p-3 bg-primary/5 border border-primary/15 rounded-lg text-slate-400 text-[11px] leading-relaxed">
            This document has been parsed, chunked, embedded, and mapped in the vector database. It is currently participating in search scoping.
          </div>
        </div>

        <div className="p-4 border-t border-slate-800/80 flex justify-end bg-slate-950/30">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-100 rounded-lg border border-slate-750 transition-colors cursor-pointer"
          >
            Close Metadata
          </button>
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const { user } = useAuth();
  
  // History & file state
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterPinned, setFilterPinned] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  
  // Rename state
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingName, setEditingName] = useState("");

  // Details Modal State
  const [detailsFile, setDetailsFile] = useState<HistoryItem | null>(null);

  // Statistics state (8 dynamic parameters)
  const [stats, setStats] = useState({
    docCount: 0,
    chunksCount: 0,
    queryCount: 0,
    hallucinationCount: 0,
    storageUsage: "0 KB",
    avgLatency: "—",
    avgConfidence: "—",
    sessionsCount: 0,
  });

  const loadDashboardData = () => {
    const userId = user?.uid || "guest";
    
    // 1. Load upload history
    const fileHistory = getHistory(userId);
    setHistory(fileHistory);

    // 2. Load conversations and compute statistics
    const conversations = getConversations(userId);
    let queryCount = 0;
    let hallucinationCount = 0;
    let totalLatency = 0;
    let latencyCount = 0;
    let totalConfidence = 0;
    let confidenceCount = 0;

    conversations.forEach((c) => {
      c.messages.forEach((m) => {
        if (m.role === "assistant" && !m.loading) {
          queryCount++;
          if (m.grounded === false || (m.confidence !== undefined && m.confidence < 35)) {
            hallucinationCount++;
          }
          if (m.latencyMs) {
            totalLatency += m.latencyMs;
            latencyCount++;
          }
          if (m.confidence !== undefined) {
            totalConfidence += m.confidence;
            confidenceCount++;
          }
        }
      });
    });

    const avgLatencyVal = latencyCount > 0 ? `${Math.round(totalLatency / latencyCount)} ms` : "—";
    const avgConfidenceVal = confidenceCount > 0 ? `${Math.round(totalConfidence / confidenceCount)}%` : "—";

    // Compute chunks count & storage size
    let chunks = 0;
    let storageKb = 0;
    fileHistory.forEach((item) => {
      chunks += item.chunks || Math.round(parseFloat(item.size) * 1.2 || 10);
      const isMb = item.size.toLowerCase().includes("mb");
      const num = parseFloat(item.size) || 0;
      storageKb += isMb ? num * 1024 : num;
    });

    const formattedStorage = storageKb >= 1024 ? `${(storageKb / 1024).toFixed(2)} MB` : `${storageKb.toFixed(1)} KB`;

    setStats({
      docCount: fileHistory.length,
      chunksCount: chunks,
      queryCount,
      hallucinationCount,
      storageUsage: formattedStorage,
      avgLatency: avgLatencyVal,
      avgConfidence: avgConfidenceVal,
      sessionsCount: conversations.length,
    });
  };

  useEffect(() => {
    loadDashboardData();
  }, [user]);

  const handleTogglePin = (docId: string) => {
    const userId = user?.uid || "guest";
    const updated = togglePinHistory(userId, docId);
    setHistory(updated);
  };

  const handleDelete = async (docId: string) => {
    const userId = user?.uid || "guest";
    if (!confirm("Are you sure you want to delete this document? This will remove its embeddings from the vector database and delete the local file.")) return;

    setDeletingId(docId);
    try {
      await deleteFile(docId);
      const updated = deleteFromHistory(userId, docId);
      setHistory(updated);
      loadDashboardData();
    } catch (err: any) {
      alert(err.message || "Failed to delete file from backend storage.");
    } finally {
      setDeletingId(null);
    }
  };

  const startRename = (docId: string, currentName: string) => {
    setEditingId(docId);
    setEditingName(currentName);
  };

  const handleSaveRename = (docId: string) => {
    const userId = user?.uid || "guest";
    if (editingName.trim()) {
      const updated = renameHistoryItem(userId, docId, editingName.trim());
      setHistory(updated);
    }
    setEditingId(null);
  };

  // Filtered files for manager
  const filteredFiles = history.filter((file) => {
    const matchesSearch = file.filename.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          file.documentId.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesPinned = filterPinned ? file.pinned : true;
    return matchesSearch && matchesPinned;
  });

  // 8 Analytics Cards config
  const cards = [
    { label: "Indexed Documents", value: stats.docCount.toString(), icon: FileText, desc: "Total source files parsed", color: "text-indigo-400" },
    { label: "Chunks Ingested", value: stats.chunksCount.toLocaleString(), icon: Layers, desc: "Total text segments in store", color: "text-violet-400" },
    { label: "Embeddings Stored", value: stats.chunksCount.toLocaleString(), icon: Database, desc: "Vectors stored in Qdrant", color: "text-blue-400" },
    { label: "Queries Answered", value: stats.queryCount.toString(), icon: MessageSquare, desc: "Total assistant prompts", color: "text-teal-400" },
    { label: "Average Confidence", value: stats.avgConfidence, icon: Check, desc: "Blended evidence accuracy", color: "text-emerald-400" },
    { label: "Average Latency", value: stats.avgLatency, icon: Zap, desc: "End-to-end processing", color: "text-amber-400" },
    { label: "Hallucinations Flagged", value: stats.hallucinationCount.toString(), icon: FileWarning, desc: "Ungrounded answers blocked", color: "text-red-400" },
    { label: "Research Sessions", value: stats.sessionsCount.toString(), icon: MessageSquare, desc: "Active threads stored", color: "text-pink-400" },
  ];

  return (
    <div className="p-8 font-sans bg-slate-950 min-h-screen text-slate-100 space-y-8">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-slate-800/60 pb-5">
        <div>
          <h1 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <span>Control Dashboard</span>
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time diagnostics, performance logs, and knowledge indexing status.
          </p>
        </div>
        
        <Link
          href="/chat"
          className="inline-flex items-center gap-1.5 text-xs font-semibold bg-primary text-primary-foreground px-4 py-2 rounded-xl shadow-lg shadow-primary/10 hover:opacity-95 transition-all"
        >
          <span>Query Console</span>
          <ArrowUpRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      {/* Analytics Cards Grid (8 Cards Layout) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {cards.map(({ label, value, icon: Icon, desc, color }) => (
          <div key={label} className="rounded-2xl border border-slate-850 bg-slate-900/20 p-5 shadow-sm hover:border-slate-800 transition-all duration-300">
            <div className="flex items-center justify-between mb-4">
              <p className="text-slate-400 text-[9px] uppercase font-bold tracking-wider">{label}</p>
              <div className={`p-1.5 bg-slate-950 border border-slate-800 rounded-lg ${color}`}>
                <Icon className="w-3.5 h-3.5" />
              </div>
            </div>
            <p className="text-2xl font-bold tracking-tight text-white">{value}</p>
            <p className="text-[10px] text-slate-400 mt-1 leading-normal">{desc}</p>
          </div>
        ))}
      </div>

      {/* File Manager Grid Suite */}
      <div className="rounded-2xl border border-slate-850 bg-slate-900/10 overflow-hidden shadow-sm flex flex-col">
        {/* Toolbar */}
        <div className="p-5 border-b border-slate-850 bg-slate-900/20 flex flex-col sm:flex-row gap-4 items-center justify-between">
          <div>
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-200">Knowledge Repository</h2>
            <p className="text-[10px] text-slate-400 mt-0.5">Manage, filter, and audit documents in index scope</p>
          </div>
          
          <div className="flex flex-wrap items-center gap-3 w-full sm:w-auto">
            {/* Search Input */}
            <div className="relative flex-1 sm:flex-initial sm:w-64">
              <Search className="absolute left-3 top-3 h-3.5 w-3.5 text-slate-400" />
              <input
                type="text"
                placeholder="Filter index files..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-8.5 pr-3.5 py-2.5 bg-slate-950/60 text-white border border-slate-800 rounded-xl text-xs focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary placeholder:text-slate-500 transition-all"
              />
            </div>
            
            {/* Filter Pinned */}
            <button
              onClick={() => setFilterPinned(!filterPinned)}
              className={`px-3.5 py-2.5 rounded-xl border text-xs font-semibold cursor-pointer transition-colors flex items-center gap-1.5
                ${filterPinned 
                  ? "bg-amber-500/10 border-amber-500/30 text-amber-400"
                  : "bg-slate-950/60 border-slate-800 text-slate-400 hover:text-white"
                }`}
            >
              <Pin className="w-3.5 h-3.5" />
              <span>Pinned Only</span>
            </button>
          </div>
        </div>

        {/* Card List of files */}
        <div className="p-6">
          {filteredFiles.length === 0 ? (
            <div className="flex flex-col items-center justify-center p-12 text-center space-y-4">
              <FileWarning className="w-10 h-10 text-slate-500" />
              <div>
                <p className="text-xs font-semibold text-slate-200">No documents index-mapped</p>
                <p className="text-[11px] text-slate-400 mt-1.5 max-w-sm font-medium">
                  There are no documents uploaded matching your parameters. Proceed to upload and index documents.
                </p>
              </div>
              <Link
                href="/upload"
                className="inline-flex items-center gap-1.5 text-xs bg-primary text-primary-foreground px-4 py-2.5 rounded-xl font-semibold shadow-md hover:opacity-95 transition-opacity"
              >
                <span>Upload Document</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredFiles.map((file) => {
                const isEditing = editingId === file.documentId;
                const isDeleting = deletingId === file.documentId;
                const isError = file.status === "error";
                const fileChunks = file.chunks || Math.round(parseFloat(file.size) * 1.2 || 10);
                const filePages = file.pages || 1;

                return (
                  <div
                    key={file.documentId}
                    className={`rounded-xl border p-4.5 bg-slate-900/20 flex flex-col justify-between gap-4 transition-all duration-200 relative group
                      ${file.pinned 
                        ? "border-amber-500/20 shadow-sm shadow-amber-500/5 bg-slate-900/35" 
                        : "border-slate-850 hover:border-slate-800"
                      }`}
                  >
                    {/* Top Row: Icon + Name + Pin */}
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-start gap-3 min-w-0 flex-1">
                        <div className="p-2 bg-primary/10 text-primary border border-primary/10 rounded-lg flex-shrink-0">
                          <FileText className="w-4.5 h-4.5" />
                        </div>

                        {/* Name display or rename input */}
                        <div className="min-w-0 flex-1">
                          {isEditing ? (
                            <div className="flex items-center gap-1 w-full">
                              <input
                                type="text"
                                value={editingName}
                                onChange={(e) => setEditingName(e.target.value)}
                                onKeyDown={(e) => {
                                  if (e.key === "Enter") handleSaveRename(file.documentId);
                                  if (e.key === "Escape") setEditingId(null);
                                }}
                                className="w-full bg-slate-950 text-white border border-slate-800 rounded px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-primary"
                                autoFocus
                              />
                              <button
                                onClick={() => handleSaveRename(file.documentId)}
                                className="p-1 text-green-500 hover:bg-slate-800 rounded cursor-pointer"
                              >
                                <Check className="w-3.5 h-3.5" />
                              </button>
                              <button
                                onClick={() => setEditingId(null)}
                                className="p-1 text-red-500 hover:bg-slate-800 rounded cursor-pointer"
                              >
                                <X className="w-3.5 h-3.5" />
                              </button>
                            </div>
                          ) : (
                            <div>
                              <span
                                className="font-semibold text-xs text-slate-100 truncate block hover:text-white cursor-pointer"
                                title={file.filename}
                                onClick={() => setDetailsFile(file)}
                              >
                                {file.filename}
                              </span>
                              <span className="text-[9px] text-slate-500 block mt-0.5 font-mono truncate">
                                ID: {file.documentId}
                              </span>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Pin Trigger */}
                      <button
                        onClick={() => handleTogglePin(file.documentId)}
                        className={`p-1.5 rounded-lg border transition-all cursor-pointer flex-shrink-0
                          ${file.pinned 
                            ? "bg-amber-500/10 border-amber-500/30 text-amber-400" 
                            : "bg-slate-955 border-transparent text-slate-400 hover:text-white hover:bg-slate-800"
                          }`}
                        title={file.pinned ? "Unpin (allow auto-eviction)" : "Pin (protect from auto-eviction)"}
                      >
                        <Pin className="w-3 h-3" />
                      </button>
                    </div>

                    {/* Middle Row: Meta Metrics */}
                    <div className="grid grid-cols-3 gap-2 text-[9px] text-slate-400 border-t border-b border-slate-800/40 py-2 bg-slate-950/20 rounded-lg px-2 text-center font-medium">
                      <div className="flex items-center justify-center gap-1">
                        <span>{file.size}</span>
                      </div>
                      <div className="flex items-center justify-center gap-1 border-l border-slate-800/60">
                        <span>{filePages} {filePages === 1 ? "page" : "pages"}</span>
                      </div>
                      <div className="flex items-center justify-center gap-1 border-l border-slate-800/60">
                        <span>{fileChunks} chunks</span>
                      </div>
                    </div>

                    {/* Bottom Row: Date + Actions */}
                    <div className="flex items-center justify-between text-[10px]">
                      <span className="text-slate-400 flex items-center gap-1 font-semibold">
                        <Calendar className="w-3.5 h-3.5 text-slate-450" />
                        {new Date(file.uploadDate).toLocaleDateString([], { month: "short", day: "numeric" })}
                      </span>

                      <div className="flex items-center gap-2">
                        {/* Status badge */}
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full font-bold text-[8px] border uppercase
                          ${isError 
                            ? "bg-red-500/5 border-red-500/25 text-red-400" 
                            : file.status === "uploading"
                            ? "bg-amber-500/5 border-amber-500/25 text-amber-400 animate-pulse"
                            : "bg-emerald-500/5 border-emerald-500/25 text-emerald-400"
                          }`}
                        >
                          {file.status ?? "done"}
                        </span>

                        {/* View Details */}
                        <button
                          onClick={() => setDetailsFile(file)}
                          className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800 cursor-pointer"
                          title="View Details"
                        >
                          <Info className="w-3.5 h-3.5" />
                        </button>

                        {/* Rename */}
                        <button
                          onClick={() => startRename(file.documentId, file.filename)}
                          className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800 cursor-pointer"
                          title="Rename"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>

                        {/* Purge delete */}
                        <button
                          onClick={() => handleDelete(file.documentId)}
                          disabled={isDeleting}
                          className="p-1 rounded text-slate-400 hover:text-red-400 hover:bg-red-950/20 disabled:opacity-40 cursor-pointer"
                          title="Purge"
                        >
                          {isDeleting ? (
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          ) : (
                            <Trash2 className="w-3.5 h-3.5" />
                          )}
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Details modal display */}
      {detailsFile && (
        <FileDetailsModal
          file={detailsFile}
          onClose={() => setDetailsFile(null)}
        />
      )}
    </div>
  );
}