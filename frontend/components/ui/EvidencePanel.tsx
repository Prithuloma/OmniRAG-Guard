"use client";

import { useState } from "react";
import {
  ChevronDown,
  ChevronUp,
  FileText,
  Activity,
  Cpu,
  Layers,
  ExternalLink,
  ShieldCheck,
  HelpCircle,
  Database
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { getHistory } from "@/lib/history";
import DocumentPreviewModal from "../chat/DocumentPreviewModal";
import { Evidence } from "@/lib/conversations";

interface EvidencePanelProps {
  evidence: Evidence[];
  groundingScore?: number; // 0 to 100
  evidenceScore?: number;   // 0 to 100
  latencyMs?: number;
  searchTimeMs?: number;
  rerankTimeMs?: number;
  verificationReason?: string;
  query?: string;
}

export default function EvidencePanel({
  evidence,
  groundingScore = 0,
  evidenceScore = 0,
  latencyMs = 0,
  searchTimeMs = 0,
  rerankTimeMs = 0,
  verificationReason = "",
  query = "",
}: EvidencePanelProps) {
  const { user } = useAuth();
  const [expandedIds, setExpandedIds] = useState<string[]>([]);
  const [whyOpen, setWhyOpen] = useState(false);
  
  // State for preview modal
  const [previewItem, setPreviewItem] = useState<{
    filename: string;
    pageNumber: number;
    chunkText: string;
    relevance: number;
  } | null>(null);

  if (evidence.length === 0) return null;

  // Resolve filename from history using user UID
  const getDocFilename = (docId: string) => {
    if (!user) return docId;
    const history = getHistory(user.uid);
    const matched = history.find((h) => h.documentId === docId);
    return matched ? matched.filename : docId;
  };

  const toggleExpand = (id: string) => {
    if (expandedIds.includes(id)) {
      setExpandedIds(expandedIds.filter((x) => x !== id));
    } else {
      setExpandedIds([...expandedIds, id]);
    }
  };

  // Helper to render matching query terms
  const renderSnippetHighlight = (text: string, search: string) => {
    if (!search || !search.trim()) return `"${text}"`;
    
    // Split search into words and escape special regex characters
    const words = search
      .split(/\s+/)
      .filter((w) => w.length > 2)
      .map((w) => w.replace(/[-\/\\^$*+?.()|[\]{}]/g, "\\$&"));

    if (words.length === 0) return `"${text}"`;

    const pattern = new RegExp(`\\b(${words.join("|")})\\b`, "gi");
    const parts = text.split(pattern);

    return (
      <span>
        "
        {parts.map((part, i) => {
          const isMatch = pattern.test(part);
          return isMatch ? (
            <mark key={i} className="bg-amber-500/20 text-amber-300 border-b border-amber-500/30 px-0.5 rounded">
              {part}
            </mark>
          ) : (
            part
          );
        })}
        "
      </span>
    );
  };

  return (
    <div className="mt-4 border-t border-border pt-4 space-y-4 font-sans">
      {/* Sources Header */}
      <div>
        <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider mb-2.5">
          Retrieval Sources ({evidence.length})
        </p>
        
        {/* Source Cards */}
        <div className="space-y-2">
          {evidence.map((e) => {
            const isExpanded = expandedIds.includes(e.id);
            const filename = getDocFilename(e.document_id || "");
            
            return (
              <div
                key={e.id}
                className="bg-slate-900/40 hover:bg-slate-900/75 border border-border/80 rounded-xl overflow-hidden transition-all duration-200"
              >
                {/* Header card action */}
                <div
                  onClick={() => toggleExpand(e.id)}
                  className="flex items-center justify-between p-3.5 cursor-pointer select-none text-xs"
                >
                  <div className="flex items-center gap-2.5 min-w-0 flex-1">
                    <FileText className="w-4 h-4 text-primary flex-shrink-0" />
                    <div className="min-w-0 flex-1">
                      <span className="font-semibold text-slate-200 truncate block">
                        {filename}
                      </span>
                      <span className="text-[10px] text-muted-foreground/60 block mt-0.5">
                        Page {(e.page_number && e.page_number > 0) ? e.page_number : "N/A"}
                      </span>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-3.5 ml-3 flex-shrink-0">
                    <span className="text-[10px] font-semibold text-emerald-400 bg-emerald-500/5 px-2.5 py-0.5 rounded-full border border-emerald-500/20">
                      {e.relevance}% Match
                    </span>
                    {isExpanded ? (
                      <ChevronUp className="w-4 h-4 text-muted-foreground/60" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-muted-foreground/60" />
                    )}
                  </div>
                </div>

                {/* Expanded Snippet Content */}
                {isExpanded && (
                  <div className="px-4 pb-4 pt-1 border-t border-border/40 bg-slate-950/30 space-y-3">
                    <div className="text-xs text-muted-foreground/95 leading-relaxed font-sans select-text italic">
                      {renderSnippetHighlight(e.chunk, query)}
                    </div>
                    <div className="flex justify-end pt-1">
                      <button
                        onClick={(event) => {
                          event.stopPropagation();
                          setPreviewItem({
                            filename,
                            pageNumber: e.page_number || 0,
                            chunkText: e.chunk,
                            relevance: e.relevance,
                          });
                        }}
                        className="flex items-center gap-1.5 px-3 py-1.5 text-[10px] bg-slate-900 hover:bg-slate-800 text-slate-200 rounded-lg border border-border/80 hover:border-border transition-all font-semibold cursor-pointer"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                        <span>Interactive Preview</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* "Why this answer?" Explanation Section */}
      <div className="bg-slate-900/35 border border-border/60 rounded-xl overflow-hidden">
        <button
          onClick={() => setWhyOpen(!whyOpen)}
          className="flex items-center justify-between w-full p-3.5 text-xs font-semibold text-muted-foreground/85 hover:bg-slate-900/50 hover:text-foreground transition-all duration-200 select-none cursor-pointer"
        >
          <div className="flex items-center gap-2">
            <HelpCircle className="w-4 h-4 text-primary" />
            <span>"Why This Answer?" Diagnostics</span>
          </div>
          {whyOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>

        {whyOpen && (
          <div className="p-4 border-t border-border bg-slate-950/20 space-y-4">
            {/* Performance Stats Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {/* Grounding Score */}
              <div className="bg-slate-900/50 border border-border p-2.5 rounded-lg flex flex-col gap-1.5">
                <span className="text-[9px] text-muted-foreground/60 uppercase font-bold tracking-wider">
                  Grounding Index
                </span>
                <span className="text-xs font-semibold text-emerald-400">
                  {groundingScore}%
                </span>
                <span className="text-[9px] text-muted-foreground/50 leading-normal">
                  Semantic coverage of generation context.
                </span>
              </div>

              {/* Consensus Score */}
              <div className="bg-slate-900/50 border border-border p-2.5 rounded-lg flex flex-col gap-1.5">
                <span className="text-[9px] text-muted-foreground/60 uppercase font-bold tracking-wider">
                  Consensus
                </span>
                <span className="text-xs font-semibold text-amber-400">
                  {evidenceScore}%
                </span>
                <span className="text-[9px] text-muted-foreground/50 leading-normal">
                  Lexical evidence overlap across chunks.
                </span>
              </div>

              {/* Total Latency */}
              <div className="bg-slate-900/50 border border-border p-2.5 rounded-lg flex flex-col gap-1.5 col-span-2 sm:col-span-1">
                <span className="text-[9px] text-muted-foreground/60 uppercase font-bold tracking-wider">
                  Pipeline Latency
                </span>
                <span className="text-xs font-semibold text-primary">
                  {latencyMs.toFixed(0)} ms
                </span>
                <span className="text-[9px] text-muted-foreground/50 leading-normal">
                  Total response latency.
                </span>
              </div>
            </div>

            {/* Sub-pipelines metrics */}
            <div className="border border-border/60 rounded-xl p-3.5 bg-slate-950/45 space-y-2.5">
              <div className="flex items-center gap-1.5 text-[9px] text-muted-foreground font-bold uppercase tracking-wider">
                <Activity className="w-3.5 h-3.5 text-primary" />
                <span>RAG Retrieval Diagnostics Breakdown</span>
              </div>
              
              <div className="space-y-2 text-xs">
                {/* Search Database */}
                <div className="flex justify-between items-center text-muted-foreground/80">
                  <span className="flex items-center gap-1.5">
                    <Database className="w-3 h-3 text-muted-foreground/60" />
                    Vector Index Query
                  </span>
                  <span className="font-mono text-[10px] text-foreground">{searchTimeMs.toFixed(1)} ms</span>
                </div>
                {/* Reranker */}
                <div className="flex justify-between items-center text-muted-foreground/80">
                  <span className="flex items-center gap-1.5">
                    <Layers className="w-3 h-3 text-muted-foreground/60" />
                    Cross-Encoder Reranking
                  </span>
                  <span className="font-mono text-[10px] text-foreground">{rerankTimeMs.toFixed(1)} ms</span>
                </div>
                {/* Generator */}
                <div className="flex justify-between items-center text-muted-foreground/80">
                  <span className="flex items-center gap-1.5">
                    <Cpu className="w-3 h-3 text-muted-foreground/60" />
                    Answer & Verification Inference
                  </span>
                  <span className="font-mono text-[10px] text-foreground">
                    {(latencyMs - searchTimeMs - rerankTimeMs).toFixed(1)} ms
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Context preview modal */}
      {previewItem && (
        <DocumentPreviewModal
          isOpen={true}
          onClose={() => setPreviewItem(null)}
          filename={previewItem.filename}
          pageNumber={previewItem.pageNumber}
          chunkText={previewItem.chunkText}
          relevance={previewItem.relevance}
          query={query}
        />
      )}
    </div>
  );
}