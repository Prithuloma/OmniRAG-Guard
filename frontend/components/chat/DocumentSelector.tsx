"use client";

import { useState, useEffect } from "react";
import { Search, FileText, CheckSquare, Square, Pin, SlidersHorizontal } from "lucide-react";
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
    <div className="w-80 border-l border-border bg-card flex flex-col h-full flex-shrink-0">
      <div className="p-4 border-b border-border flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-2">
          <SlidersHorizontal className="w-4 h-4 text-primary" />
          <h2 className="text-sm font-semibold">Search Scope</h2>
        </div>
        <span className="text-[10px] bg-primary/10 text-primary px-2 py-0.5 rounded-full font-medium">
          {selectedIds.length} / {history.length} Selected
        </span>
      </div>

      {/* Search Input */}
      <div className="p-3 border-b border-border flex-shrink-0">
        <div className="relative">
          <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
          <input
            type="text"
            placeholder="Filter documents..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-8 pr-3 py-1.5 bg-background text-foreground border border-border rounded-md text-xs focus:outline-none focus:ring-1 focus:ring-primary placeholder:text-muted-foreground/60"
          />
        </div>
      </div>

      {/* Select buttons */}
      <div className="px-3 py-2 border-b border-border flex gap-2 justify-between flex-shrink-0">
        <button
          onClick={handleSelectAll}
          className="text-xs text-primary hover:underline font-medium cursor-pointer"
        >
          Select All
        </button>
        <button
          onClick={handleDeselectAll}
          className="text-xs text-muted-foreground hover:text-foreground hover:underline font-medium cursor-pointer"
        >
          Deselect All
        </button>
      </div>

      {/* Scrollable list */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {filteredHistory.length === 0 ? (
          <div className="text-center py-8 px-4">
            <FileText className="w-8 h-8 text-muted-foreground/40 mx-auto mb-2" />
            <p className="text-xs text-muted-foreground">
              {searchTerm ? "No matching documents found" : "No uploaded documents yet"}
            </p>
          </div>
        ) : (
          filteredHistory.map((item) => {
            const isChecked = selectedIds.includes(item.documentId);
            return (
              <div
                key={item.documentId}
                onClick={() => handleToggle(item.documentId)}
                className={`flex items-center justify-between p-2.5 rounded-lg border transition-all duration-200 cursor-pointer select-none
                  ${isChecked
                    ? "bg-primary/5 border-primary/20 text-foreground"
                    : "border-transparent text-muted-foreground hover:bg-accent/40 hover:text-foreground"
                  }`}
              >
                <div className="flex items-center gap-2.5 min-w-0 flex-1">
                  <div className="flex-shrink-0">
                    {isChecked ? (
                      <CheckSquare className="w-4 h-4 text-primary" />
                    ) : (
                      <Square className="w-4 h-4 text-muted-foreground/60" />
                    )}
                  </div>
                  <FileText className={`w-4 h-4 flex-shrink-0 ${isChecked ? "text-primary" : "text-muted-foreground/60"}`} />
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-medium truncate">{item.filename}</p>
                    <p className="text-[10px] text-muted-foreground/60 font-mono mt-0.5">{item.size}</p>
                  </div>
                </div>
                {item.pinned && (
                  <span title="Pinned file">
                    <Pin className="w-3 h-3 text-amber-500/80 flex-shrink-0 ml-1.5" />
                  </span>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
