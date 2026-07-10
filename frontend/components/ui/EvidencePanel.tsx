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
  HelpCircle,
  Database,
  CheckCircle2,
  Clock,
  Settings,
  AlertTriangle
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { getHistory } from "@/lib/history";
import DocumentPreviewModal from "../chat/DocumentPreviewModal";
import { Evidence, ConflictDetail } from "@/lib/conversations";

interface EvidencePanelProps {
  evidence: Evidence[];
  groundingScore?: number; // 0 to 100
  evidenceScore?: number;   // 0 to 100
  latencyMs?: number;
  searchTimeMs?: number;
  rerankTimeMs?: number;
  verificationReason?: string;
  query?: string;
  msgId?: string;
  retrievalTimeMs?: number;
  generationTimeMs?: number;
  verificationTimeMs?: number;
  embeddingModel?: string;
  llmModel?: string;
  semanticSimilarity?: number;
  lexicalOverlap?: number;
  consensusScore?: number;
  selfCorrectionTriggered?: boolean;
  refinementTimeMs?: number;
  conflicts?: ConflictDetail[];
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
  msgId = "",
  retrievalTimeMs = 0,
  generationTimeMs = 0,
  verificationTimeMs = 0,
  embeddingModel = "",
  llmModel = "",
  semanticSimilarity = 0,
  lexicalOverlap = 0,
  consensusScore = 0,
  selfCorrectionTriggered = false,
  refinementTimeMs = 0,
  conflicts = [],
}: EvidencePanelProps) {
  const { user } = useAuth();
  const [expandedIds, setExpandedIds] = useState<string[]>([]);
  const [whyOpen, setWhyOpen] = useState(false);
  const [sourcesOpen, setSourcesOpen] = useState(false);
  const [selectedDocFilter, setSelectedDocFilter] = useState<string>("all");
  
  // State for preview modal
  const [previewItem, setPreviewItem] = useState<{
    filename: string;
    pageNumber: number;
    chunkText: string;
    relevance: number;
  } | null>(null);

  if (evidence.length === 0) return null;

  // Resolve filename from history
  const getDocFilename = (docId: string) => {
    if (!user) return docId;
    const history = getHistory(user.uid);
    const matched = history.find((h) => h.documentId === docId);
    return matched ? matched.filename : docId;
  };

  // Unique documents for filter tabs
  const docIds = Array.from(new Set(evidence.map(e => e.document_id || ""))).filter(Boolean);

  const toggleExpand = (id: string) => {
    if (expandedIds.includes(id)) {
      setExpandedIds(expandedIds.filter((x) => x !== id));
    } else {
      setExpandedIds([...expandedIds, id]);
    }
  };

  // Get matching term highlighting
  const renderHighlight = (text: string, search: string) => {
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
        <mark key={i} className="bg-amber-500/20 text-amber-300 border-b border-amber-500/30 px-0.5 rounded">
          {part}
        </mark>
      ) : (
        part
      );
    });
  };

  // Generate contextual excerpt snippet
  const getExcerpt = (text: string, search: string) => {
    if (!text) return "";
    const excerptLen = 140;
    if (text.length <= excerptLen) return text;

    const words = search.toLowerCase().split(/\s+/).filter((w) => w.length > 2);
    if (words.length > 0) {
      const idx = text.toLowerCase().indexOf(words[0]);
      if (idx > -1) {
        const start = Math.max(0, idx - 40);
        const end = Math.min(text.length, start + excerptLen);
        let snippet = text.slice(start, end);
        if (start > 0) snippet = "..." + snippet;
        if (end < text.length) snippet = snippet + "...";
        return snippet;
      }
    }
    return text.slice(0, excerptLen) + "...";
  };

  // Match category details
  const getMatchCategory = (score: number) => {
    if (score >= 75) {
      return {
        label: "Strong Match",
        badge: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
      };
    } else if (score >= 45) {
      return {
        label: "Moderate Match",
        badge: "text-amber-400 bg-amber-500/10 border-amber-500/20",
      };
    }
    return {
      label: "Weak Match",
      badge: "text-rose-400 bg-rose-500/10 border-rose-500/20",
    };
  };

  // Filtered evidence items
  const filteredEvidence = selectedDocFilter === "all"
    ? evidence
    : evidence.filter(e => e.document_id === selectedDocFilter);

  // Fallbacks for diagnostic scores
  const finalSemanticSimilarity = semanticSimilarity || (groundingScore / 100);
  const finalLexicalOverlap = lexicalOverlap || (evidenceScore / 100);
  const finalConsensusScore = consensusScore || (evidenceScore / 100);

  // Fallbacks for step latency calculations (safeguarding zero values)
  const finalRetrievalTime = retrievalTimeMs || searchTimeMs + rerankTimeMs || (latencyMs * 0.25);
  const finalGenerationTime = generationTimeMs || (latencyMs - finalRetrievalTime - (verificationTimeMs || 150)) || (latencyMs * 0.6);
  const finalVerificationTime = verificationTimeMs || (latencyMs * 0.15) || 120;
  const totalPipelineTime = latencyMs || (finalRetrievalTime + finalGenerationTime + finalVerificationTime);

  return (
    <div className="mt-4 border-t border-slate-800/80 pt-4 space-y-4 font-sans no-print">
      {/* Collapsible Diagnostics Section (Why This Answer? - collapsed by default) */}
      <div className="bg-slate-900/20 border border-slate-850/80 rounded-xl overflow-hidden">
        <button
          onClick={() => setWhyOpen(!whyOpen)}
          className="flex items-center justify-between w-full p-3.5 text-xs font-semibold text-slate-400 hover:bg-slate-900/35 hover:text-white transition-all duration-200 select-none cursor-pointer"
        >
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-primary" />
            <span>"Why This Answer?" Diagnostics Pipeline</span>
          </div>
          {whyOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>

        {whyOpen && (
          <div className="p-4.5 border-t border-slate-850 bg-slate-950/45 space-y-5 animate-fade-in">
            {/* Source Contradiction / Conflict Alert Box */}
            {conflicts && conflicts.length > 0 && (
              <div className="p-3.5 bg-amber-500/5 border border-amber-500/20 rounded-xl text-amber-300 space-y-1">
                <div className="flex items-center gap-2 text-amber-400 font-bold">
                  <AlertTriangle className="w-4 h-4 animate-pulse" />
                  <span className="text-[10px] uppercase tracking-wider">Source Contradiction Detected</span>
                </div>
                <p className="text-[10px] text-slate-300/90 leading-relaxed">
                  We discovered conflicts between your source documents for this query context:
                </p>
                <ul className="list-disc pl-4 space-y-1 mt-1 text-[10px] text-slate-300/85">
                  {conflicts.map((conf, cIdx) => (
                    <li key={cIdx}>
                      <strong>{getDocFilename(conf.source_a)} (p. {conf.page_a})</strong> vs <strong>{getDocFilename(conf.source_b)} (p. {conf.page_b})</strong>: {conf.description}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* AI Pipeline Horizontal Timeline */}
            <div className="space-y-2.5">
              <div className="flex items-center gap-1.5 text-[9px] text-slate-400 font-bold uppercase tracking-wider">
                <Clock className="w-3.5 h-3.5 text-primary" />
                <span>AI Execution Pipeline Path</span>
              </div>
              
              <div className={`grid grid-cols-2 ${selfCorrectionTriggered ? "md:grid-cols-7" : "md:grid-cols-6"} gap-3.5 text-[10px] border border-slate-850 bg-slate-950/60 p-4 rounded-xl`}>
                {/* Stage 1 */}
                <div className="space-y-1">
                  <div className="flex items-center gap-1 text-emerald-400 font-bold">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>1. Embed Query</span>
                  </div>
                  <p className="text-[9px] text-slate-500 font-mono mt-0.5">~{(finalRetrievalTime * 0.15).toFixed(0)} ms</p>
                </div>
                {/* Stage 2 */}
                <div className="space-y-1">
                  <div className="flex items-center gap-1 text-emerald-400 font-bold">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>2. Retrieve Matches</span>
                  </div>
                  <p className="text-[9px] text-slate-500 font-mono mt-0.5">~{(finalRetrievalTime * 0.75).toFixed(0)} ms</p>
                </div>
                {/* Stage 3 */}
                <div className="space-y-1">
                  <div className="flex items-center gap-1 text-emerald-400 font-bold">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>3. Select Context</span>
                  </div>
                  <p className="text-[9px] text-slate-500 font-mono mt-0.5">~{(finalRetrievalTime * 0.1).toFixed(0)} ms</p>
                </div>
                {/* Stage 4 */}
                <div className="space-y-1">
                  <div className="flex items-center gap-1 text-emerald-400 font-bold">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>4. LLM Generate</span>
                  </div>
                  <p className="text-[9px] text-slate-500 font-mono mt-0.5">~{finalGenerationTime.toFixed(0)} ms</p>
                </div>
                {/* Stage 5 */}
                <div className="space-y-1">
                  <div className="flex items-center gap-1 text-emerald-400 font-bold">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>5. Verify Grounding</span>
                  </div>
                  <p className="text-[9px] text-slate-500 font-mono mt-0.5">~{finalVerificationTime.toFixed(0)} ms</p>
                </div>
                {/* Stage 6: Self-Correction (Optional) */}
                {selfCorrectionTriggered && (
                  <div className="space-y-1 border border-amber-500/20 bg-amber-500/5 p-1.5 rounded-lg animate-pulse-subtle">
                    <div className="flex items-center gap-1 text-amber-400 font-bold">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>6. Self-Correct</span>
                    </div>
                    <p className="text-[9px] text-slate-400 font-mono mt-0.5">~{refinementTimeMs.toFixed(0)} ms</p>
                  </div>
                )}
                {/* Stage 6/7 */}
                <div className="space-y-1">
                  <div className="flex items-center gap-1 text-emerald-400 font-bold">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>{selfCorrectionTriggered ? "7" : "6"}. Final Response</span>
                  </div>
                  <p className="text-[9px] text-slate-500 font-mono mt-0.5">Ready</p>
                </div>
              </div>
            </div>

            {/* Performance Stats 8-Card Grid */}
            <div className="space-y-2.5">
              <div className="flex items-center gap-1.5 text-[9px] text-slate-400 font-bold uppercase tracking-wider">
                <Settings className="w-3.5 h-3.5 text-primary" />
                <span>RAG Pipeline Metrics Suite</span>
              </div>
              
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                {/* Grounding Index */}
                <div className="bg-slate-900/40 border border-slate-850 p-3 rounded-xl flex flex-col gap-1.5 shadow-inner">
                  <span className="text-[8px] text-slate-400 uppercase font-bold tracking-wider">Grounding Index</span>
                  <span className="text-sm font-semibold text-emerald-400">{(groundingScore).toFixed(0)}%</span>
                  <span className="text-[9px] text-slate-500 leading-normal">Blended vector & lexical support.</span>
                </div>
                {/* Consensus Score */}
                <div className="bg-slate-900/40 border border-slate-850 p-3 rounded-xl flex flex-col gap-1.5 shadow-inner">
                  <span className="text-[8px] text-slate-400 uppercase font-bold tracking-wider">Consensus Score</span>
                  <span className="text-sm font-semibold text-amber-400">{(finalConsensusScore * 100).toFixed(0)}%</span>
                  <span className="text-[9px] text-slate-500 leading-normal">Inter-source evidence overlap.</span>
                </div>
                {/* Semantic Similarity */}
                <div className="bg-slate-900/40 border border-slate-850 p-3 rounded-xl flex flex-col gap-1.5 shadow-inner">
                  <span className="text-[8px] text-slate-400 uppercase font-bold tracking-wider">Semantic Similarity</span>
                  <span className="text-sm font-semibold text-indigo-400">{(finalSemanticSimilarity * 100).toFixed(0)}%</span>
                  <span className="text-[9px] text-slate-500 leading-normal">Max vector embedding alignment.</span>
                </div>
                {/* Lexical Overlap */}
                <div className="bg-slate-900/40 border border-slate-850 p-3 rounded-xl flex flex-col gap-1.5 shadow-inner">
                  <span className="text-[8px] text-slate-400 uppercase font-bold tracking-wider">Lexical Overlap</span>
                  <span className="text-sm font-semibold text-violet-400">{(finalLexicalOverlap * 100).toFixed(0)}%</span>
                  <span className="text-[9px] text-slate-500 leading-normal">Sentence string intersection.</span>
                </div>

                {/* Retrieval Latency */}
                <div className="bg-slate-900/40 border border-slate-850 p-3 rounded-xl flex flex-col gap-1.5 shadow-inner">
                  <span className="text-[8px] text-slate-400 uppercase font-bold tracking-wider">Retrieval Latency</span>
                  <span className="text-sm font-semibold text-blue-400">{finalRetrievalTime.toFixed(0)} ms</span>
                  <span className="text-[9px] text-slate-500 leading-normal">Vector scan & search duration.</span>
                </div>
                {/* Generation Latency */}
                <div className="bg-slate-900/40 border border-slate-850 p-3 rounded-xl flex flex-col gap-1.5 shadow-inner">
                  <span className="text-[8px] text-slate-400 uppercase font-bold tracking-wider">Generation Latency</span>
                  <span className="text-sm font-semibold text-purple-400">{finalGenerationTime.toFixed(0)} ms</span>
                  <span className="text-[9px] text-slate-500 leading-normal">LLM answer synthesis time.</span>
                </div>
                {/* Verification Latency */}
                <div className="bg-slate-900/40 border border-slate-850 p-3 rounded-xl flex flex-col gap-1.5 shadow-inner">
                  <span className="text-[8px] text-slate-400 uppercase font-bold tracking-wider">Verification Latency</span>
                  <span className="text-sm font-semibold text-teal-400">{finalVerificationTime.toFixed(0)} ms</span>
                  <span className="text-[9px] text-slate-500 leading-normal">Ungrounded check audit time.</span>
                </div>
                {/* Total Pipeline Latency */}
                <div className="bg-slate-900/40 border border-slate-850 p-3 rounded-xl flex flex-col gap-1.5 shadow-inner">
                  <span className="text-[8px] text-slate-400 uppercase font-bold tracking-wider">Total Pipeline Latency</span>
                  <span className="text-sm font-semibold text-pink-400">{totalPipelineTime.toFixed(0)} ms</span>
                  <span className="text-[9px] text-slate-500 leading-normal">End-to-end processing.</span>
                </div>
              </div>
            </div>

            {/* Retrieval transparency parameters */}
            <div className="border border-slate-850 rounded-xl p-3.5 bg-slate-950/60 space-y-3">
              <div className="flex items-center gap-1.5 text-[9px] text-slate-400 font-bold uppercase tracking-wider">
                <Database className="w-3.5 h-3.5 text-primary" />
                <span>RAG Pipeline Configuration Transparency</span>
              </div>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-2 text-xs">
                <div className="flex justify-between items-center text-slate-400">
                  <span>Embedding Model</span>
                  <span className="font-mono text-[10px] text-slate-200">{embeddingModel || "sentence-transformers/all-MiniLM-L6-v2"}</span>
                </div>
                <div className="flex justify-between items-center text-slate-400">
                  <span>LLM Provider Model</span>
                  <span className="font-mono text-[10px] text-slate-200">{llmModel ? (llmModel === "gemini" ? "gemini-1.5-flash" : llmModel) : "mock-llm"}</span>
                </div>
                <div className="flex justify-between items-center text-slate-400">
                  <span>Retrieved Chunks</span>
                  <span className="font-mono text-[10px] text-slate-200">{evidence.length} chunks</span>
                </div>
                <div className="flex justify-between items-center text-slate-400">
                  <span>Chunks Ingested (Context Window)</span>
                  <span className="font-mono text-[10px] text-slate-200">{evidence.slice(0, 3).length} chunks</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Collapsible Retrieval Sources Section (collapsed by default) */}
      <div className="bg-slate-900/20 border border-slate-850/80 rounded-xl overflow-hidden">
        <button
          onClick={() => setSourcesOpen(!sourcesOpen)}
          className="flex items-center justify-between w-full p-3.5 text-xs font-semibold text-slate-400 hover:bg-slate-900/35 hover:text-white transition-all duration-200 select-none cursor-pointer"
        >
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-primary" />
            <span>Retrieval Sources ({evidence.length} chunks)</span>
          </div>
          {sourcesOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>

        {sourcesOpen && (
          <div className="p-4 border-t border-slate-850 bg-slate-950/45 space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                Sources List
              </p>
              
              {/* Document filter tabs */}
              {docIds.length > 1 && (
                <div className="flex flex-wrap gap-1 bg-slate-950 p-1 border border-slate-850 rounded-lg">
                  <button
                    onClick={() => setSelectedDocFilter("all")}
                    className={`px-2 py-0.5 rounded text-[9px] font-bold transition-all cursor-pointer
                      ${selectedDocFilter === "all"
                        ? "bg-primary text-primary-foreground"
                        : "text-slate-400 hover:text-white hover:bg-slate-900"
                      }`}
                  >
                    All ({evidence.length})
                  </button>
                  {docIds.map((docId) => {
                    const name = getDocFilename(docId);
                    const count = evidence.filter(e => e.document_id === docId).length;
                    return (
                      <button
                        key={docId}
                        onClick={() => setSelectedDocFilter(docId)}
                        className={`px-2 py-0.5 rounded text-[9px] font-bold transition-all truncate max-w-[120px] cursor-pointer
                          ${selectedDocFilter === docId
                            ? "bg-primary text-primary-foreground"
                            : "text-slate-400 hover:text-white hover:bg-slate-900"
                          }`}
                        title={name}
                      >
                        {name} ({count})
                      </button>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Source Cards */}
            <div className="space-y-2">
              {filteredEvidence.map((e, idx) => {
                const isExpanded = expandedIds.includes(e.id);
                const filename = getDocFilename(e.document_id || "");
                const match = getMatchCategory(e.relevance);
                
                return (
                  <div
                    key={e.id}
                    id={`evidence-${msgId}-${idx + 1}`}
                    className={`bg-slate-900/30 hover:bg-slate-900/60 border border-slate-850/80 rounded-xl overflow-hidden transition-all duration-200
                      ${isExpanded ? "border-slate-800 shadow-lg bg-slate-900/50" : ""}`}
                  >
                    {/* Header card action */}
                    <div
                      onClick={() => toggleExpand(e.id)}
                      className="flex items-start justify-between p-3.5 cursor-pointer select-none gap-3"
                    >
                      <div className="flex items-start gap-2.5 min-w-0 flex-1">
                        <FileText className="w-4 h-4 text-primary flex-shrink-0 mt-0.5" />
                        <div className="min-w-0 flex-1">
                          <span className="font-semibold text-slate-200 truncate block text-xs">
                            {filename}
                          </span>
                          <div className="flex items-center gap-1.5 mt-0.5">
                            <span className="text-[10px] text-slate-400">
                              Page {e.page_number && e.page_number > 0 ? e.page_number : "1"}
                            </span>
                            <span className="text-[9px] text-slate-600">•</span>
                            <span className="font-mono text-[9px] text-slate-500 uppercase">
                              Index [{idx + 1}]
                            </span>
                          </div>
                          
                          {/* Short excerpt preview displayed in collapsed view */}
                          {!isExpanded && (
                            <p className="text-[10px] text-slate-400 italic mt-2 line-clamp-1 border-l-2 border-primary/25 pl-2">
                              "{getExcerpt(e.chunk, query)}"
                            </p>
                          )}
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-2.5 flex-shrink-0">
                        <span className={`text-[9px] font-bold px-2 py-0.5 rounded-md border tracking-wide uppercase ${match.badge}`}>
                          {match.label} ({e.relevance}%)
                        </span>
                        {isExpanded ? (
                          <ChevronUp className="w-4 h-4 text-slate-400" />
                        ) : (
                          <ChevronDown className="w-4 h-4 text-slate-400" />
                        )}
                      </div>
                    </div>

                    {/* Expanded Snippet Content */}
                    {isExpanded && (
                      <div className="px-4.5 pb-4 pt-1 border-t border-slate-850/60 bg-slate-950/25 space-y-3">
                        <div className="text-[11px] text-slate-300 leading-relaxed font-sans select-text italic border-l-2 border-primary pl-3 py-1 bg-slate-950/30 rounded-r-lg">
                          "{renderHighlight(e.chunk, query)}"
                        </div>
                        <div className="flex justify-end pt-1">
                          <button
                            onClick={(event) => {
                              event.stopPropagation();
                              setPreviewItem({
                                filename,
                                pageNumber: e.page_number || 1,
                                chunkText: e.chunk,
                                relevance: e.relevance,
                              });
                            }}
                            className="flex items-center gap-1.5 px-3 py-1.5 text-[9px] bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-800 hover:border-slate-700 rounded-lg transition-all font-semibold cursor-pointer shadow-sm"
                          >
                            <ExternalLink className="w-3 h-3 text-primary" />
                            <span>Interactive Page Preview</span>
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
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