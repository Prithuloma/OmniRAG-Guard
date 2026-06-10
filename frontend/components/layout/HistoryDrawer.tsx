"use client";

import { useAuth } from "@/context/AuthContext";
import { getHistory, HistoryItem } from "@/lib/history";
import { useEffect, useState } from "react";
import { X, FileText, Calendar, HardDrive, Inbox } from "lucide-react";

export default function HistoryDrawer() {
  const { user, isHistoryOpen, setHistoryOpen } = useAuth();
  const [history, setHistory] = useState<HistoryItem[]>([]);

  useEffect(() => {
    if (user && isHistoryOpen) {
      setHistory(getHistory(user.uid));
    }
  }, [user, isHistoryOpen]);

  if (!isHistoryOpen) return null;

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
        className="absolute inset-0 bg-slate-950/40 backdrop-blur-sm transition-opacity duration-300"
        onClick={() => setHistoryOpen(false)}
      />

      {/* Sliding panel */}
      <div className="absolute inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-md bg-slate-900/95 border-l border-slate-800/80 text-slate-100 shadow-2xl flex flex-col backdrop-blur-xl transition-all duration-300 transform">
          {/* Header */}
          <div className="px-6 py-5 border-b border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Inbox className="w-5 h-5 text-indigo-400" />
              <h2 className="text-lg font-semibold tracking-wide">Upload History</h2>
            </div>
            <button
              onClick={() => setHistoryOpen(false)}
              className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-slate-100 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Subtitle */}
          <div className="px-6 py-3 bg-slate-950/30 text-xs text-slate-400 border-b border-slate-800">
            Displaying your last 10 uploads. Document queries are filtered to search only these files.
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {history.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center py-12">
                <div className="w-12 h-12 rounded-full bg-slate-800/50 flex items-center justify-center text-slate-500 mb-4 border border-slate-800">
                  <FileText className="w-6 h-6" />
                </div>
                <p className="text-sm font-medium text-slate-300">No upload history found</p>
                <p className="text-xs text-slate-500 mt-1 max-w-xs">
                  Files you upload will appear here and will be accessible to you in the chat.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {history.map((item) => (
                  <div
                    key={item.documentId}
                    className="group relative rounded-xl border border-slate-800/60 bg-slate-950/20 hover:bg-slate-950/45 hover:border-slate-800 p-4 transition-all duration-200"
                  >
                    <div className="flex items-start gap-3">
                      <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/10 shadow-inner group-hover:bg-indigo-500/15 transition-colors">
                        <FileText className="w-4 h-4" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-slate-200 truncate group-hover:text-white transition-colors">
                          {item.filename}
                        </p>
                        <p className="text-[10px] text-slate-500 font-mono mt-1">
                          ID: {item.documentId}
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-4 mt-3 pt-3 border-t border-slate-900 text-xs text-slate-400">
                      <div className="flex items-center gap-1.5">
                        <HardDrive className="w-3.5 h-3.5 text-slate-500" />
                        <span>{item.size}</span>
                      </div>
                      <div className="flex items-center gap-1.5 ml-auto">
                        <Calendar className="w-3.5 h-3.5 text-slate-500" />
                        <span>{formatDate(item.uploadDate)}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
