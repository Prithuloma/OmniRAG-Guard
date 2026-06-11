"use client";

import { X, FileText, Calendar, Database, ShieldAlert } from "lucide-react";

interface DocumentPreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  filename: string;
  pageNumber: number;
  chunkText: string;
  relevance: number;
  query: string;
}

export default function DocumentPreviewModal({
  isOpen,
  onClose,
  filename,
  pageNumber,
  chunkText,
  relevance,
  query,
}: DocumentPreviewModalProps) {
  if (!isOpen) return null;

  // Highlight helper
  const renderHighlightedText = (text: string, search: string) => {
    if (!search || !search.trim()) return text;
    
    // Split search into words and escape special regex characters
    const words = search
      .split(/\s+/)
      .filter((w) => w.length > 2)
      .map((w) => w.replace(/[-\/\\^$*+?.()|[\]{}]/g, "\\$&"));

    if (words.length === 0) return text;

    // Build regex pattern matching any of the words (case insensitive)
    const pattern = new RegExp(`\\b(${words.join("|")})\\b`, "gi");
    const parts = text.split(pattern);

    return parts.map((part, i) => {
      const isMatch = pattern.test(part);
      return isMatch ? (
        <mark key={i} className="bg-amber-500/20 text-amber-200 border-b border-amber-400/30 px-0.5 rounded">
          {part}
        </mark>
      ) : (
        part
      );
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm transition-opacity">
      <div className="bg-card border border-border w-full max-w-2xl rounded-xl shadow-2xl flex flex-col max-h-[85vh] overflow-hidden">
        {/* Header */}
        <div className="p-5 border-b border-border flex items-center justify-between bg-accent/20">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-lg text-primary">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-semibold text-sm truncate max-w-[400px]">
                {filename}
              </h3>
              <p className="text-xs text-muted-foreground mt-0.5">
                Page {pageNumber > 0 ? pageNumber : "N/A"} • Context Preview
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-6">
          {/* Metadata banner */}
          <div className="grid grid-cols-3 gap-4 p-3.5 bg-background border border-border rounded-lg text-xs">
            <div className="flex flex-col gap-1">
              <span className="text-muted-foreground/60 uppercase text-[9px] font-semibold tracking-wider">
                Relevance Match
              </span>
              <span className="font-medium text-emerald-400">{relevance}% Match</span>
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-muted-foreground/60 uppercase text-[9px] font-semibold tracking-wider">
                Source Type
              </span>
              <span className="font-medium">Document Chunk</span>
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-muted-foreground/60 uppercase text-[9px] font-semibold tracking-wider">
                Verification
              </span>
              <span className="font-medium flex items-center gap-1 text-primary">
                Verified Evidence
              </span>
            </div>
          </div>

          {/* Chunk Text Container */}
          <div className="space-y-2.5">
            <span className="text-xs font-semibold text-muted-foreground/80 uppercase tracking-wider">
              Document Passage
            </span>
            <div className="p-5 bg-background border border-border rounded-lg leading-relaxed text-sm font-sans whitespace-pre-wrap select-text text-foreground/90 max-h-[300px] overflow-y-auto">
              {renderHighlightedText(chunkText, query)}
            </div>
          </div>

          {/* Notice */}
          <div className="flex items-start gap-2.5 p-3 bg-primary/5 border border-primary/10 rounded-lg text-xs text-muted-foreground">
            <ShieldAlert className="w-4 h-4 text-primary flex-shrink-0 mt-0.5" />
            <p>
              This excerpt is direct ground truth extracted during document ingestion. The highlighted terms show lexical alignment with your query.
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-border flex justify-end bg-accent/10">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-medium bg-secondary text-secondary-foreground hover:bg-secondary/80 rounded-lg transition-colors cursor-pointer"
          >
            Close Preview
          </button>
        </div>
      </div>
    </div>
  );
}
