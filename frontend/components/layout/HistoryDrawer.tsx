"use client";

import { useAuth } from "@/context/AuthContext";
import { getHistory, togglePinHistory, deleteFromHistory, HistoryItem } from "@/lib/history";
import { deleteFile } from "@/services/api";
import { useEffect, useState } from "react";
import { X, FileText, Calendar, HardDrive, Inbox, Pin, Trash2, Loader2, AlertCircle } from "lucide-react";

export default function HistoryDrawer() {
  const { user, isHistoryOpen, setHistoryOpen } = useAuth();
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState("");

  const loadHistory = () => {
    if (isHistoryOpen) {
      const userId = user?.uid || "guest";
      setHistory(getHistory(userId));
    }
  };

  useEffect(() => {
    loadHistory();
  }, [user, isHistoryOpen]);

  if (!isHistoryOpen) return null;

  const handleTogglePin = (docId: string) => {
    const userId = user?.uid || "guest";
    const updated = togglePinHistory(userId, docId);
    setHistory(updated);
  };

  const handleDelete = async (docId: string) => {
    const userId = user?.uid || "guest";
    if (!confirm("Are you sure you want to delete this file? This will remove its embeddings from the database and delete it from your storage context.")) {
      return;
    }

    setDeletingId(docId);
    setErrorMsg("");

    try {
      // 1. Delete from vector store & backend
      await deleteFile(docId);
      
      // 2. Delete from local history list
      const updated = deleteFromHistory(userId, docId);
      setHistory(updated);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to purge file from backend service.");
    } finally {
      setDeletingId(null);
    }
  };

  const formatDate = (isoString: string) => {
    try {
      const date = new Date(isoString);
      return date.toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return isoString;
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden font-sans">
      {/* Backdrop overlay */}
      <div
        className="absolute inset-0 bg-slate-950/60 backdrop-blur-sm transition-opacity duration-300"
        onClick={() => setHistoryOpen(false)}
      />

      {/* Sliding panel */}
      <div className="absolute inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-md bg-slate-950 border-l border-border text-slate-100 shadow-2xl flex flex-col backdrop-blur-xl transition-all duration-300 transform">
          {/* Header */}
          <div className="px-6 py-5 border-b border-border flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <Inbox className="w-4 h-4 text-primary" />
              <h2 className="text-sm font-semibold tracking-wide">Knowledge Files (Uploads)</h2>
            </div>
            <button
              onClick={() => setHistoryOpen(false)}
              className="p-1.5 rounded-lg hover:bg-slate-900 text-muted-foreground hover:text-white border border-transparent hover:border-border/50 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Subtitle */}
          <div className="px-6 py-3 bg-slate-900/40 text-[10px] font-medium text-muted-foreground border-b border-border leading-relaxed">
            Displaying your last 20 uploads. Pinned files are excluded from auto-eviction.
          </div>

          {errorMsg && (
            <div className="mx-6 mt-4 p-3 bg-red-950/45 border border-red-800/40 text-red-300 text-[11px] rounded-xl flex items-center gap-2">
              <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {history.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center py-12">
                <div className="w-12 h-12 rounded-2xl bg-slate-900 flex items-center justify-center text-muted-foreground mb-4 border border-border">
                  <FileText className="w-5 h-5 text-primary" />
                </div>
                <p className="text-xs font-semibold text-slate-300">No indexed documents</p>
                <p className="text-[11px] text-muted-foreground mt-1 max-w-xs leading-normal">
                  Uploaded files will appear here and will participate in search indexing.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {history.map((item) => {
                  const isDeleting = deletingId === item.documentId;
                  return (
                    <div
                      key={item.documentId}
                      className="group relative rounded-xl border border-border/70 bg-slate-900/30 hover:bg-slate-900/60 p-4 transition-all duration-200"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex items-start gap-3 min-w-0">
                          <div className="p-2 rounded-lg bg-primary/10 text-primary border border-primary/10 shadow-inner group-hover:bg-primary/15 transition-colors flex-shrink-0">
                            <FileText className="w-4 h-4" />
                          </div>
                          <div className="min-w-0">
                            <p className="text-xs font-semibold text-slate-200 truncate group-hover:text-white transition-colors">
                              {item.filename}
                            </p>
                            <p className="text-[9px] text-muted-foreground/50 font-mono mt-0.5 truncate">
                              ID: {item.documentId}
                            </p>
                          </div>
                        </div>

                        {/* Pin and Delete Controls */}
                        <div className="flex items-center gap-1.5 flex-shrink-0">
                          <button
                            onClick={() => handleTogglePin(item.documentId)}
                            className={`p-1.5 rounded-lg border transition-all cursor-pointer ${
                              item.pinned
                                ? "bg-amber-500/10 border-amber-500/30 text-amber-400"
                                : "bg-transparent border-transparent text-muted-foreground/60 hover:text-white hover:bg-slate-800"
                            }`}
                            title={item.pinned ? "Unpin file (allow auto-eviction)" : "Pin file (prevent auto-eviction)"}
                          >
                            <Pin className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={() => handleDelete(item.documentId)}
                            disabled={isDeleting}
                            className="p-1.5 rounded-lg border border-transparent text-muted-foreground/60 hover:text-red-400 hover:bg-red-950/20 disabled:opacity-40 transition-all cursor-pointer"
                            title="Delete file"
                          >
                            {isDeleting ? (
                              <Loader2 className="w-3.5 h-3.5 animate-spin" />
                            ) : (
                              <Trash2 className="w-3.5 h-3.5" />
                            )}
                          </button>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-4 mt-3.5 pt-3 border-t border-border/40 text-[10px] text-muted-foreground">
                        <div className="flex items-center gap-1.5">
                          <HardDrive className="w-3 h-3 text-muted-foreground/60" />
                          <span>{item.size}</span>
                        </div>
                        {item.status && (
                          <div className={`px-2 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider border ${
                            item.status === "done" 
                              ? "bg-emerald-500/5 border-emerald-500/25 text-emerald-400" 
                              : item.status === "error"
                              ? "bg-red-500/5 border-red-500/25 text-red-400"
                              : "bg-amber-500/5 border-amber-500/25 text-amber-400 animate-pulse"
                          }`}>
                            {item.status}
                          </div>
                        )}
                        <div className="flex items-center gap-1.5 ml-auto">
                          <Calendar className="w-3 h-3 text-muted-foreground/60" />
                          <span>{formatDate(item.uploadDate)}</span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
