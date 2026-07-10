"use client";

import { useState, useEffect } from "react";
import { Search, FileText, CheckSquare, Square, Pin, SlidersHorizontal, Calendar, Layers } from "lucide-react";
import { getHistory, HistoryItem } from "@/lib/history";

interface DocumentSelectorProps {
  userId: string;
  selectedIds: string[];
  onChange: (ids: string[]) => void;
}

export default function DocumentSelector({
  userId,
  selectedIds,
  onChange,
}: DocumentSelectorProps) {
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [searchTerm, setSearchTerm] = useState("");

  // Load history from localStorage
  useEffect(() => {
    setHistory(getHistory(userId).filter((h) => h.status === "done"));
  }, [userId]);

  const filteredHistory = history.filter((item) =>
    item.filename.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleToggle = (docId: string) => {
    if (selectedIds.includes(docId)) {
      onChange(selectedIds.filter((id) => id !== docId));
    } else {
      onChange([...selectedIds, docId]);
    }
  };

  const handleSelectAll = () => {
    onChange(filteredHistory.map((h) => h.documentId));
  };

  const handleDeselectAll = () => {
    onChange([]);
  };

  return (
    <div className="w-80 border-l border-slate-800/80 bg-slate-900/10 flex flex-col h-full flex-shrink-0 font-sans z-10 backdrop-blur-md">
      <div className="p-4 border-b border-slate-800/80 flex items-center justify-between flex-shrink-0 bg-slate-950/20">
        <div className="flex items-center gap-2">
          <SlidersHorizontal className="w-4 h-4 text-primary" />
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-200">Search Scope</h2>
        </div>
        <span className="text-[10px] bg-primary/10 text-primary border border-primary/20 px-2.5 py-0.5 rounded-full font-bold">
          {selectedIds.length} / {history.length} Selected
        </span>
      </div>

      {/* Search Input */}
      <div className="p-3 border-b border-slate-800/80 flex-shrink-0 bg-slate-950/10">
        <div className="relative">
          <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-slate-400" />
          <input
            type="text"
            placeholder="Filter documents by name..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-8 pr-3 py-2 bg-slate-950/60 text-slate-205 text-slate-200 border border-slate-800/80 rounded-xl text-xs focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary placeholder:text-slate-500 transition-all"
          />
        </div>
      </div>

      {/* Select buttons */}
      <div className="px-3.5 py-2.5 border-b border-slate-800/80 flex gap-2 justify-between flex-shrink-0 bg-slate-950/5 text-[10px]">
        <button
          onClick={handleSelectAll}
          className="text-primary hover:text-white transition-colors font-bold uppercase tracking-wider cursor-pointer"
        >
          Select All
        </button>
        <button
          onClick={handleDeselectAll}
          className="text-slate-400 hover:text-slate-205 hover:text-slate-200 transition-colors font-bold uppercase tracking-wider cursor-pointer"
        >
          Deselect All
        </button>
      </div>

      {/* Scrollable list */}
      <div className="flex-1 overflow-y-auto p-3.5 space-y-2.5 bg-slate-950/15">
        {filteredHistory.length === 0 ? (
          <div className="text-center py-12 px-4 space-y-3">
            <div className="p-3 bg-slate-900 border border-slate-800/60 rounded-2xl inline-flex text-slate-500">
              <FileText className="w-6 h-6" />
            </div>
            <p className="text-xs text-slate-400 font-semibold">
              {searchTerm ? "No matching documents found" : "No uploaded documents yet"}
            </p>
          </div>
        ) : (
          filteredHistory.map((item) => {
            const isChecked = selectedIds.includes(item.documentId);
            const sizeStr = item.size;
            // Fallback chunks calculation
            const chunksCount = item.chunks || Math.round(parseFloat(item.size) * 1.2 || 10);
            const pagesCount = item.pages || 1;
            
            return (
              <div
                key={item.documentId}
                onClick={() => handleToggle(item.documentId)}
                className={`flex flex-col gap-2 p-3 rounded-xl border transition-all duration-200 cursor-pointer select-none
                  ${isChecked
                    ? "bg-primary/5 border-primary/30 text-white shadow-md shadow-primary/5"
                    : "border-slate-850 bg-slate-900/15 text-slate-400 hover:bg-slate-900/35 hover:border-slate-805 hover:border-slate-800"
                  }`}
              >
                <div className="flex items-start justify-between gap-2.5 min-w-0">
                  <div className="flex items-start gap-2.5 min-w-0 flex-1">
                    <div className="flex-shrink-0 mt-0.5">
                      {isChecked ? (
                        <CheckSquare className="w-4 h-4 text-primary" />
                      ) : (
                        <Square className="w-4 h-4 text-slate-500" />
                      )}
                    </div>
                    <FileText className={`w-4 h-4 flex-shrink-0 mt-0.5 ${isChecked ? "text-primary" : "text-slate-500"}`} />
                    <div className="min-w-0 flex-1">
                      <p className={`text-xs font-semibold truncate leading-tight ${isChecked ? "text-slate-100" : "text-slate-300"}`}>
                        {item.filename}
                      </p>
                      <span className="text-[9px] text-slate-500 font-mono block mt-1 truncate">
                        ID: {item.documentId}
                      </span>
                    </div>
                  </div>
                  {item.pinned && (
                    <span title="Pinned file" className="flex-shrink-0">
                      <Pin className="w-3.5 h-3.5 text-amber-500 flex-shrink-0 mt-0.5" />
                    </span>
                  )}
                </div>
                
                {/* Details layout: size, pages, chunks, date */}
                <div className="border-t border-slate-800/40 pt-2 flex flex-wrap gap-x-2.5 gap-y-1 text-[9px] text-slate-500/90 font-medium">
                  <span className="font-mono text-slate-405 text-slate-400">{sizeStr}</span>
                  <span>•</span>
                  <span>{pagesCount} {pagesCount === 1 ? "page" : "pages"}</span>
                  <span>•</span>
                  <span className="flex items-center gap-0.5">
                    <Layers className="w-2.5 h-2.5" />
                    {chunksCount} chunks
                  </span>
                  <span>•</span>
                  <span className="flex items-center gap-0.5">
                    <Calendar className="w-2.5 h-2.5" />
                    {new Date(item.uploadDate).toLocaleDateString([], { month: "short", day: "numeric" })}
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
