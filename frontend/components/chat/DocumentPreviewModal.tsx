"use client";

import { useEffect, useRef } from "react";
import { X, FileText, ShieldAlert } from "lucide-react";

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
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen && scrollContainerRef.current) {
      const timer = setTimeout(() => {
        const firstMarkElement = scrollContainerRef.current?.querySelector("mark");
        if (firstMarkElement) {
          firstMarkElement.scrollIntoView({ behavior: "smooth", block: "center" });
        }
      }, 200);
      return () => clearTimeout(timer);
    }
  }, [isOpen, chunkText, query]);

  if (!isOpen) return null;

  // Highlight helper
  const renderHighlightedText = (text: string, search: string) => {
    if (!search || !search.trim()) return text;
    
    const words = search
      .split(/\s+/)
      .filter((w) => w.length > 2)
      .map((w) => w.replace(/[-\/\\^$*+?.()|[\]{}]/g, "\\$&"));

    if (words.length === 0) return text;
    const pattern = new RegExp(`\\b(${words.join("|")})\\b`, "gi");
    const parts = text.split(pattern);

    return parts.map((part, i) => {
      const isMatch = pattern.test(part);
      return isMatch ? (
        <mark key={i} className="bg-amber-500/20 text-amber-200 border-b border-amber-400/30 px-0.5 rounded transition-all duration-300">
          {part}
        </mark>
      ) : (
        part
      );
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm transition-opacity">
      <div className="bg-slate-900 border border-slate-800/80 w-full max-w-2xl rounded-xl shadow-2xl flex flex-col max-h-[85vh] overflow-hidden font-sans">
        {/* Header */}
        <div className="p-5 border-b border-slate-800/60 flex items-center justify-between bg-slate-950/30">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-lg text-primary">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-semibold text-sm truncate max-w-[400px] text-slate-100">
                {filename}
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Page {pageNumber > 0 ? pageNumber : "1"} • Context Preview
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 border border-transparent hover:border-slate-800 transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-6">
          {/* Metadata banner */}
          <div className="grid grid-cols-3 gap-4 p-3.5 bg-slate-950/40 border border-slate-800/80 rounded-xl text-xs">
            <div className="flex flex-col gap-1">
              <span className="text-slate-400 uppercase text-[9px] font-bold tracking-wider">
                Relevance Match
              </span>
              <span className="font-semibold text-emerald-405 text-emerald-400">{relevance}% Match</span>
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-slate-400 uppercase text-[9px] font-bold tracking-wider">
                Source Type
              </span>
              <span className="font-semibold text-slate-200">Document Chunk</span>
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-slate-400 uppercase text-[9px] font-bold tracking-wider">
                Verification
              </span>
              <span className="font-semibold flex items-center gap-1 text-primary">
                Verified Evidence
              </span>
            </div>
          </div>

          {/* Chunk Text Container */}
          <div className="space-y-2.5">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              Document Passage
            </span>
            <div
              ref={scrollContainerRef}
              className="p-5 bg-slate-950/50 border border-slate-800/60 rounded-xl leading-relaxed text-sm font-sans whitespace-pre-wrap select-text text-slate-200 max-h-[300px] overflow-y-auto"
            >
              {renderHighlightedText(chunkText, query)}
            </div>
          </div>

          {/* Notice */}
          <div className="flex items-start gap-2.5 p-3.5 bg-primary/5 border border-primary/10 rounded-xl text-xs text-slate-300">
            <ShieldAlert className="w-4 h-4 text-primary flex-shrink-0 mt-0.5" />
            <p className="leading-relaxed">
              This excerpt is direct ground truth extracted during document ingestion. The highlighted terms show lexical alignment with your query. The viewer automatically scrolled to the matching sentence.
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800/60 flex justify-end bg-slate-950/20">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-100 rounded-lg border border-slate-700 transition-colors cursor-pointer"
          >
            Close Preview
          </button>
        </div>
      </div>
    </div>
  );
}
