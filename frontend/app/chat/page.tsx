"use client";

import { useState, useEffect, useRef, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import ChatInput from "@/components/chat/ChatInput";
import VerificationPanel from "@/components/ui/VerificationPanel";
import EvidencePanel from "@/components/ui/EvidencePanel";
import { queryRAG } from "@/services/api";
import { useAuth } from "@/context/AuthContext";
import { getHistory } from "@/lib/history";
import {
  getConversations,
  saveConversation,
  Conversation,
  Message,
  Evidence,
  ClaimVerification
} from "@/lib/conversations";
import DocumentSelector from "@/components/chat/DocumentSelector";
import {
  Sparkles,
  ArrowRight,
  Loader2,
  CheckCircle2,
  Info,
  User,
  Shield,
  FileText,
  Clock,
  Database,
  Download,
  Printer,
  ChevronDown,
  AlertTriangle
} from "lucide-react";

// Visualizer steps for pipeline (6 loading stages)
const PIPELINE_STEPS = [
  { label: "Searching documents...", desc: "Scanning document repository" },
  { label: "Computing embeddings...", desc: "Embedding query text with sentence-transformers" },
  { label: "Retrieving context...", desc: "Fetching vector matches from Qdrant" },
  { label: "Generating answer...", desc: "Synthesizing response via Gemini 1.5 Flash" },
  { label: "Verifying grounding...", desc: "Performing lexical and semantic verification checks" },
  { label: "Preparing response...", desc: "Formatting output and final citations" },
];

const ONBOARDING_PROMPTS = [
  { text: "Summarize this document", desc: "Generate a structured high-level abstract" },
  { text: "Explain the key concepts", desc: "Break down main definitions and terms" },
  { text: "List important takeaways", desc: "Extract bullet points of core metrics" },
  { text: "Generate interview questions", desc: "Create a quiz based on document facts" },
  { text: "Compare uploaded documents", desc: "Identify differences between sources" },
  { text: "Find contradictions", desc: "Flag inconsistent metrics or claims" },
  { text: "Create revision notes", desc: "Synthesize summary study cards" }
];

// Custom Formatted Markdown Renderer with clickable Inline Citation Badges
function FormattedMarkdown({
  content,
  msgId,
  claims,
  onCitationClick
}: {
  content: string;
  msgId: string;
  claims?: ClaimVerification[];
  onCitationClick: (idx: number) => void;
}) {
  if (!content) return null;

  const lines = content.split("\n");
  const elements: React.ReactNode[] = [];

  const parseLine = (text: string) => {
    if (!text) return "";
    
    const parts: React.ReactNode[] = [];
    const regex = /(\*\*.*?\*\*|\[\d+\])/g;
    const splitParts = text.split(regex);
    
    splitParts.forEach((part, i) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        parts.push(<strong key={i} className="font-bold text-white">{part.slice(2, -2)}</strong>);
      } else if (part.match(/^\[\d+\]$/)) {
        const num = parseInt(part.slice(1, -1));
        parts.push(
          <button
            key={i}
            onClick={() => onCitationClick(num)}
            className="inline-flex items-center justify-center w-4 h-4 text-[9px] font-bold bg-primary/20 hover:bg-primary text-primary hover:text-primary-foreground rounded-full border border-primary/20 transition-all cursor-pointer mx-0.5"
            title={`Jump to Source [${num}]`}
          >
            {num}
          </button>
        );
      } else {
        parts.push(part);
      }
    });
    return parts;
  };

  const renderParagraphWithClaims = (paragraphText: string, pIdx: number) => {
    if (!claims || claims.length === 0) {
      return (
        <p key={pIdx} className="text-xs leading-relaxed text-slate-300 mb-3">
          {parseLine(paragraphText)}
        </p>
      );
    }

    const sentences = paragraphText.split(/(?<=\.|\?|!)\s+/);
    
    const renderedSentences = sentences.map((sentence, sIdx) => {
      const trimmed = sentence.trim();
      if (!trimmed) return null;

      const cleanSentence = trimmed.replace(/\*\*|\*/g, "");

      const matchingClaim = claims.find(c => {
        const cleanClaim = c.text.replace(/\*\*|\*/g, "").toLowerCase();
        return cleanClaim.includes(cleanSentence.toLowerCase()) || 
               cleanSentence.toLowerCase().includes(cleanClaim);
      });

      if (!matchingClaim) {
        return <span key={sIdx}>{parseLine(sentence)} </span>;
      }

      let borderClass = "";
      let statusLabel = "";
      let bgHover = "";
      if (matchingClaim.status === "grounded") {
        borderClass = "border-b border-dashed border-emerald-500/70";
        statusLabel = "Grounded Claim";
        bgHover = "hover:bg-emerald-500/5";
      } else if (matchingClaim.status === "partially_grounded") {
        borderClass = "border-b border-dotted border-amber-500/70";
        statusLabel = "Partially Grounded Claim";
        bgHover = "hover:bg-amber-500/5";
      } else {
        borderClass = "border-b border-dashed border-red-500/70";
        statusLabel = "Ungrounded Assertion Alert";
        bgHover = "hover:bg-red-500/5";
      }

      const citationIndices = matchingClaim.citations.map(cit => cit.source_index).join(", ");
      const tooltipText = `${statusLabel} (Score: ${Math.round(matchingClaim.grounding_score * 100)}%) ${citationIndices ? `• Sources: [${citationIndices}]` : '• No citations'}`;

      return (
        <span
          key={sIdx}
          className={`${borderClass} ${bgHover} transition-all duration-200 cursor-help px-0.5 inline rounded-sm`}
          title={tooltipText}
        >
          {parseLine(sentence)}
          {" "}
        </span>
      );
    });

    return (
      <p key={pIdx} className="text-xs leading-relaxed text-slate-300 mb-3">
        {renderedSentences}
      </p>
    );
  };

  let inList = false;
  let listItems: React.ReactNode[] = [];

  lines.forEach((line, idx) => {
    const trimmed = line.trim();
    if (trimmed.startsWith("###")) {
      if (inList) {
        elements.push(<ul key={`list-${idx}`} className="space-y-1.5 my-3 list-disc pl-5">{listItems}</ul>);
        inList = false;
        listItems = [];
      }
      elements.push(
        <h3 key={idx} className="text-xs font-bold text-slate-100 mt-5 mb-2.5 uppercase tracking-wider border-b border-slate-800 pb-1">
          {parseLine(trimmed.slice(3).trim())}
        </h3>
      );
    } else if (trimmed.startsWith("##")) {
      if (inList) {
        elements.push(<ul key={`list-${idx}`} className="space-y-1.5 my-3 list-disc pl-5">{listItems}</ul>);
        inList = false;
        listItems = [];
      }
      elements.push(
        <h2 key={idx} className="text-sm font-bold text-white mt-6 mb-3 border-b border-slate-800 pb-1">
          {parseLine(trimmed.slice(2).trim())}
        </h2>
      );
    } else if (trimmed.startsWith("-") || trimmed.startsWith("*")) {
      inList = true;
      listItems.push(
        <li key={`li-${idx}`} className="text-xs leading-relaxed text-slate-300">
          {parseLine(trimmed.slice(1).trim())}
        </li>
      );
    } else if (trimmed === "") {
      if (inList) {
        elements.push(<ul key={`list-${idx}`} className="space-y-1.5 my-3 list-disc pl-5">{listItems}</ul>);
        inList = false;
        listItems = [];
      }
    } else {
      if (inList) {
        elements.push(<ul key={`list-${idx}`} className="space-y-1.5 my-3 list-disc pl-5">{listItems}</ul>);
        inList = false;
        listItems = [];
      }
      elements.push(renderParagraphWithClaims(line, idx));
    }
  });

  if (inList) {
    elements.push(<ul key="list-end" className="space-y-1.5 my-3 list-disc pl-5">{listItems}</ul>);
  }

  return <div className="space-y-1">{elements}</div>;
}

function ChatContent() {
  const { user } = useAuth();
  const searchParams = useSearchParams();
  const router = useRouter();
  const activeChatId = searchParams.get("id");

  const [messages, setMessages] = useState<Message[]>([]);
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const [loadingStep, setLoadingStep] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  
  // Dropdown states
  const [activeExportId, setActiveExportId] = useState<string | null>(null);
  const [headerExportOpen, setHeaderExportOpen] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const loadingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const printAreaRef = useRef<HTMLDivElement>(null);

  // Initialize selected document IDs
  useEffect(() => {
    if (user) {
      const history = getHistory(user.uid).filter((h) => h.status === "done");
      setSelectedDocIds(history.map((h) => h.documentId));
    }
  }, [user]);

  // Load conversation on ID change
  useEffect(() => {
    if (!user) return;
    if (activeChatId) {
      const conversations = getConversations(user.uid);
      const match = conversations.find((c) => c.id === activeChatId);
      if (match) {
        setMessages(match.messages);
      } else {
        setMessages([]);
      }
    } else {
      setMessages([]);
    }
  }, [user, activeChatId]);

  // Auto Scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading, loadingStep]);

  // Clean visualizer interval on unmount
  useEffect(() => {
    return () => {
      if (loadingIntervalRef.current) clearInterval(loadingIntervalRef.current);
    };
  }, []);

  // Resolve filename helper
  const getDocFilename = (docId: string) => {
    if (!user) return docId;
    const history = getHistory(user.uid);
    const matched = history.find((h) => h.documentId === docId);
    return matched ? matched.filename : docId;
  };

  // Click scroll to cited source card
  const scrollToEvidence = (citationIndex: number, msgId: string) => {
    const el = document.getElementById(`evidence-${msgId}-${citationIndex}`);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "center" });
      el.classList.add("ring-2", "ring-primary", "bg-primary/10");
      setTimeout(() => {
        el.classList.remove("ring-2", "ring-primary", "bg-primary/10");
      }, 2000);
    }
  };

  // Export handlers
  const exportAnswerMarkdown = (msg: Message) => {
    let text = `# RAG Answer: ${msg.content.slice(0, 30)}\n\n`;
    text += `${msg.content}\n\n`;
    if (msg.evidence && msg.evidence.length > 0) {
      text += `## Sources Cited\n`;
      msg.evidence.forEach((ev, idx) => {
        const name = getDocFilename(ev.document_id || "");
        text += `[${idx + 1}] ${name} (page ${ev.page_number || 1})\n`;
      });
    }
    const blob = new Blob([text], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `answer-${msg.id}.md`;
    a.click();
    URL.revokeObjectURL(url);
    setActiveExportId(null);
  };

  const exportConversationMarkdown = () => {
    if (messages.length === 0) return;
    const activeConv = getConversations(user?.uid || "").find((c) => c.id === activeChatId);
    const title = activeConv ? activeConv.title : "OmniRAG Conversation";
    
    let text = `# RAG Conversation: ${title}\n\n`;
    messages.forEach((msg) => {
      text += `### ${msg.role.toUpperCase()} (${msg.timestamp})\n\n`;
      text += `${msg.content}\n\n`;
      if (msg.evidence && msg.evidence.length > 0) {
        text += `Sources:\n`;
        msg.evidence.forEach((ev, idx) => {
          const name = getDocFilename(ev.document_id || "");
          text += `- [${idx + 1}] ${name} (page ${ev.page_number || 1})\n`;
        });
        text += `\n`;
      }
    });
    
    const blob = new Blob([text], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `conversation-${activeChatId || Date.now()}.md`;
    a.click();
    URL.revokeObjectURL(url);
    setHeaderExportOpen(false);
  };

  const printAnswer = (msg: Message) => {
    // Add print wrapper styling and trigger print
    const printWindow = window.open("", "_blank");
    if (!printWindow) return;
    const filenameList = msg.evidence?.map((ev, idx) => {
      const name = getDocFilename(ev.document_id || "");
      return `<li>[${idx + 1}] ${name} (page ${ev.page_number || 1})</li>`;
    }).join("") || "";

    printWindow.document.write(`
      <html>
        <head>
          <title>OmniRAG-Guard Answer PDF Export</title>
          <style>
            body { font-family: system-ui, sans-serif; padding: 40px; color: #1e293b; line-height: 1.6; }
            h2 { color: #0f172a; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px; margin-top: 30px; }
            h3 { color: #334155; margin-top: 24px; font-size: 1.1em; }
            li { margin-bottom: 8px; }
            .meta { font-size: 0.85em; color: #64748b; margin-bottom: 20px; }
            .alert { background: #fef3c7; border-left: 4px solid #f59e0b; padding: 12px; font-size: 0.9em; margin-bottom: 20px; border-radius: 4px; }
          </style>
        </head>
        <body>
          <div class="meta">OmniRAG-Guard Grounded QA Audit Report • ID: ${msg.id} • Generated at: ${new Date().toLocaleString()}</div>
          ${(msg.confidence && msg.confidence < 35) ? '<div class="alert">⚠️ Warning: Blended evidence confidence score falls below 35% validation threshold. Assertions may lack robust document support.</div>' : ''}
          <div style="font-size: 0.95em;">
            ${msg.content.replace(/\n/g, "<br/>")}
          </div>
          ${filenameList ? `<h2>Sources Cited</h2><ul>${filenameList}</ul>` : ""}
          <script>window.onload = function() { window.print(); window.close(); }</script>
        </body>
      </html>
    `);
    printWindow.document.close();
    setActiveExportId(null);
  };

  const printConversation = () => {
    if (messages.length === 0) return;
    const activeConv = getConversations(user?.uid || "").find((c) => c.id === activeChatId);
    const title = activeConv ? activeConv.title : "OmniRAG Conversation";
    
    const printWindow = window.open("", "_blank");
    if (!printWindow) return;
    
    let contentHtml = "";
    messages.forEach((msg) => {
      const roleName = msg.role === "user" ? "User Request" : "AI Response";
      contentHtml += `
        <div style="margin-bottom: 30px; padding-bottom: 20px; border-bottom: 1px solid #f1f5f9;">
          <h3 style="margin-bottom: 5px;">${roleName} <span style="font-size:0.75em; font-weight:normal; color:#94a3b8;">(${msg.timestamp})</span></h3>
          <div>${msg.content.replace(/\n/g, "<br/>")}</div>
        </div>
      `;
    });

    printWindow.document.write(`
      <html>
        <head>
          <title>${title}</title>
          <style>
            body { font-family: system-ui, sans-serif; padding: 40px; color: #1e293b; line-height: 1.6; }
            h1 { color: #0f172a; border-bottom: 2px solid #cbd5e1; padding-bottom: 12px; font-size: 1.8em; }
            h3 { color: #0f172a; }
          </style>
        </head>
        <body>
          <h1>RAG Session Log: ${title}</h1>
          <div style="font-size: 0.85em; color: #64748b; margin-bottom: 30px;">OmniRAG-Guard Research Export • Date: ${new Date().toLocaleString()}</div>
          ${contentHtml}
          <script>window.onload = function() { window.print(); window.close(); }</script>
        </body>
      </html>
    `);
    printWindow.document.close();
    setHeaderExportOpen(false);
  };

  const handleSend = async (content: string) => {
    if (!user) return;
    setIsLoading(true);
    setLoadingStep(0);

    const chatId = activeChatId || Date.now().toString();
    const chatTitle = activeChatId
      ? undefined
      : content.slice(0, 35) + (content.length > 35 ? "..." : "");

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);

    // Simulate progress visualizer steps sequentially
    if (loadingIntervalRef.current) clearInterval(loadingIntervalRef.current);
    loadingIntervalRef.current = setInterval(() => {
      setLoadingStep((prev) => {
        if (prev < PIPELINE_STEPS.length - 1) {
          return prev + 1;
        }
        return prev;
      });
    }, 800);

    try {
      // Safe scoping search logic
      const filters = {
        document_ids: selectedDocIds.length > 0 ? selectedDocIds : ["doc_none_uploaded_yet"]
      };

      const data = await queryRAG(content, 3, filters);

      if (loadingIntervalRef.current) {
        clearInterval(loadingIntervalRef.current);
        loadingIntervalRef.current = null;
      }
      setLoadingStep(PIPELINE_STEPS.length - 1); // Set to final complete state

      const mappedEvidence: Evidence[] = (data.retrieved_chunks ?? []).map((c: any) => ({
        id: c.chunk_id,
        source: `${c.document_id} — page ${c.page_number}`,
        chunk: c.text,
        relevance: Math.round(c.score * 100),
        document_id: c.document_id,
        page_number: c.page_number,
      }));

      // Set up typewriter message
      const botMsgId = (Date.now() + 1).toString();
      const botMsgPlaceholder: Message = {
        id: botMsgId,
        role: "assistant",
        content: "",
        confidence: Math.round((data.confidence ?? 0) * 100),
        grounded: data.grounded,
        evidence: mappedEvidence,
        groundingScore: Math.round((data.grounding_score ?? 0) * 100),
        evidenceScore: Math.round((data.evidence_score ?? 0) * 100),
        latencyMs: data.latency_ms,
        searchTimeMs: data.retrieval_stats?.search_time_ms ?? 0,
        rerankTimeMs: data.retrieval_stats?.rerank_time_ms ?? 0,
        verificationReason: data.verification_reason,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        streaming: true,
        // Expose new diagnostic metrics
        retrievalTimeMs: data.retrieval_time_ms,
        generationTimeMs: data.generation_time_ms,
        verificationTimeMs: data.verification_time_ms,
        embeddingModel: data.embedding_model,
        llmModel: data.llm_model,
        semanticSimilarity: data.semantic_similarity,
        lexicalOverlap: data.lexical_overlap,
        consensusScore: data.consensus_score,
        claims: data.claims,
        conflicts: data.conflicts,
        selfCorrectionTriggered: data.self_correction_triggered,
        refinementTimeMs: data.refinement_time_ms,
      };

      setMessages((prev) => [...prev, botMsgPlaceholder]);
      setIsLoading(false);

      // Start Typewriter effect
      let charIndex = 0;
      const fullAnswer = data.answer ?? "No answer returned.";
      const stepSize = 4; // Add 4 characters at a time for smooth performance

      const typewriterInterval = setInterval(() => {
        setMessages((prev) => {
          const next = [...prev];
          const botIdx = next.findIndex((m) => m.id === botMsgId);
          if (botIdx > -1) {
            next[botIdx] = {
              ...next[botIdx],
              content: fullAnswer.slice(0, charIndex + stepSize),
            };
          }
          return next;
        });
        charIndex += stepSize;
        if (charIndex >= fullAnswer.length) {
          clearInterval(typewriterInterval);

          setMessages((prev) => {
            const finalMessages = [...prev];
            const botIdx = finalMessages.findIndex((m) => m.id === botMsgId);
            if (botIdx > -1) {
              finalMessages[botIdx].streaming = false;
            }

            // Auto title generation lookup
            const generatedTitle = data.conversation_title || chatTitle || "Untitled Chat";

            // Save conversation state
            const currentConv: Conversation = {
              id: chatId,
              title: activeChatId ? (getConversations(user.uid).find((c) => c.id === activeChatId)?.title || "Untitled Chat") : generatedTitle,
              messages: finalMessages,
              updatedAt: new Date().toISOString(),
            };
            saveConversation(user.uid, currentConv);

            return finalMessages;
          });

          if (!activeChatId) {
            router.push(`/chat?id=${chatId}`);
          }
        }
      }, 12);

    } catch (err: any) {
      if (loadingIntervalRef.current) clearInterval(loadingIntervalRef.current);
      setIsLoading(false);
      const errMsg = err.message || "Failed to query system.";

      const botMsgError: Message = {
        id: Date.now().toString(),
        role: "assistant",
        content: errMsg,
        confidence: 0,
        grounded: false,
        evidence: [],
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, botMsgError]);
    }
  };

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 overflow-hidden font-sans">
      {/* CSS print style declarations */}
      <style dangerouslySetInnerHTML={{ __html: `
        @media print {
          body, html, main {
            background: white !important;
            color: black !important;
          }
          .no-print, header, nav, button, input {
            display: none !important;
          }
        }
      `}} />

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col h-full overflow-hidden relative">
        {/* Chat header */}
        <div className="p-4 border-b border-slate-800/80 bg-slate-900/20 backdrop-blur flex items-center justify-between flex-shrink-0 z-10">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 text-primary border border-primary/10 rounded-xl">
              <Shield className="w-4 h-4" />
            </div>
            <div>
              <h1 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                {activeChatId ? (getConversations(user?.uid || "").find((c) => c.id === activeChatId)?.title || "Secure Grounded QA") : "Secure Grounded QA"}
              </h1>
              <p className="text-[10px] text-slate-400 mt-0.5 leading-none">
                Queries verify source alignment using mathematical consensus
              </p>
            </div>
          </div>

          {/* Header Action Menu */}
          {messages.length > 0 && (
            <div className="relative">
              <button
                onClick={() => setHeaderExportOpen(!headerExportOpen)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-[10px] font-semibold text-slate-300 transition-all cursor-pointer"
              >
                <span>Export Chat</span>
                <ChevronDown className="w-3 h-3 text-slate-400" />
              </button>

              {headerExportOpen && (
                <div className="absolute right-0 mt-1.5 w-48 bg-slate-900 border border-slate-800 rounded-xl shadow-xl z-50 p-1.5 space-y-1 animate-fade-in no-print">
                  <button
                    onClick={exportConversationMarkdown}
                    className="w-full flex items-center gap-2 px-3 py-2 text-left text-[10px] text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg transition-colors cursor-pointer"
                  >
                    <Download className="w-3.5 h-3.5 text-primary" />
                    <span>Download Markdown</span>
                  </button>
                  <button
                    onClick={printConversation}
                    className="w-full flex items-center gap-2 px-3 py-2 text-left text-[10px] text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg transition-colors cursor-pointer"
                  >
                    <Printer className="w-3.5 h-3.5 text-primary" />
                    <span>Print PDF</span>
                  </button>
                  <div className="border-t border-slate-850 my-1"></div>
                  <button
                    onClick={() => setHeaderExportOpen(false)}
                    className="w-full px-3 py-1.5 text-center text-[9px] text-slate-500 hover:text-slate-400 cursor-pointer"
                  >
                    Cancel
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Message scroll container */}
        <div className="flex-1 overflow-y-auto px-6 py-8 space-y-8 bg-slate-950/45">
          {messages.length === 0 && !isLoading ? (
            <div className="h-full flex flex-col items-center justify-center text-center max-w-xl mx-auto space-y-8 animate-fade-in">
              <div className="p-4 bg-primary/10 rounded-2xl text-primary border border-primary/25 shadow-lg pulsing-ring">
                <Sparkles className="w-6 h-6" />
              </div>
              <div className="space-y-2.5">
                <h2 className="text-base font-bold tracking-tight text-white">Ask anything about your documents</h2>
                <p className="text-[11px] text-slate-400 leading-relaxed max-w-sm mx-auto">
                  OmniRAG-Guard uses semantic search, dense embedding maps, and hybrid consensus scoring to deliver evidence-backed assertions.
                </p>
              </div>

              {/* Starter Prompts */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full pt-4">
                {ONBOARDING_PROMPTS.map((prompt, i) => (
                  <button
                    key={i}
                    onClick={() => handleSend(prompt.text)}
                    className="p-3.5 text-left text-xs bg-slate-900/30 border border-slate-850/80 rounded-xl hover:bg-slate-900/80 hover:border-primary/45 hover:shadow-lg transition-all duration-200 cursor-pointer flex justify-between items-center group"
                  >
                    <div className="min-w-0 pr-2">
                      <span className="font-semibold text-slate-200 block truncate">{prompt.text}</span>
                      <span className="text-[10px] text-slate-500 block mt-0.5 truncate">{prompt.desc}</span>
                    </div>
                    <ArrowRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-primary transition-colors flex-shrink-0" />
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-8 max-w-3xl mx-auto">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex gap-4 items-start ${
                    msg.role === "user" ? "flex-row-reverse" : "flex-row"
                  } animate-fade-in`}
                >
                  {/* Avatar */}
                  <div className="flex-shrink-0">
                    {msg.role === "user" ? (
                      <div className="w-7 h-7 rounded-xl bg-primary text-primary-foreground flex items-center justify-center shadow-md">
                        <User className="w-4 h-4" />
                      </div>
                    ) : (
                      <div className="w-7 h-7 rounded-xl bg-slate-900 border border-slate-850 text-primary flex items-center justify-center shadow-md">
                        <Shield className="w-4 h-4" />
                      </div>
                    )}
                  </div>

                  {/* Bubble content */}
                  <div className="flex-1 min-w-0 max-w-[85%] space-y-1">
                    <div className={`flex items-center gap-2.5 text-[10px] font-bold text-slate-500 ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                      <span>{msg.role === "user" ? "YOU" : "SYSTEM"}</span>
                      <span>•</span>
                      <span className="font-mono text-[9px]">{msg.timestamp}</span>
                    </div>

                    <div
                      className={`rounded-2xl px-5 py-4 text-xs select-text leading-relaxed shadow-sm relative group/bubble
                        ${
                          msg.role === "user"
                            ? "bg-primary text-primary-foreground font-medium rounded-tr-none ml-auto"
                            : "bg-slate-900/40 border border-slate-850/80 text-slate-100 rounded-tl-none"
                        }`}
                    >
                      {/* Floating Export menu inside bot bubbles */}
                      {msg.role === "assistant" && !msg.loading && (
                        <div className="absolute right-3.5 top-3.5 opacity-0 group-hover/bubble:opacity-100 transition-opacity duration-200 no-print">
                          <div className="relative">
                            <button
                              onClick={() => setActiveExportId(activeExportId === msg.id ? null : msg.id)}
                              className="p-1 rounded bg-slate-950/60 border border-slate-800 hover:border-slate-700 text-slate-400 hover:text-white cursor-pointer"
                              title="Export Response"
                            >
                              <Download className="w-3.5 h-3.5" />
                            </button>

                            {activeExportId === msg.id && (
                              <div className="absolute right-0 mt-1 w-44 bg-slate-900 border border-slate-800 rounded-xl shadow-xl z-50 p-1.5 space-y-1 font-sans">
                                <button
                                  onClick={() => exportAnswerMarkdown(msg)}
                                  className="w-full flex items-center gap-2 px-2.5 py-1.5 text-left text-[9px] font-semibold text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg transition-colors cursor-pointer"
                                >
                                  <Download className="w-3 h-3 text-primary" />
                                  <span>Download Markdown</span>
                                </button>
                                <button
                                  onClick={() => printAnswer(msg)}
                                  className="w-full flex items-center gap-2 px-2.5 py-1.5 text-left text-[9px] font-semibold text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg transition-colors cursor-pointer"
                                >
                                  <Printer className="w-3 h-3 text-primary" />
                                  <span>Print PDF</span>
                                </button>
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                      {/* Dynamic Markdown Answer Formatting */}
                      {msg.role === "assistant" ? (
                        <FormattedMarkdown
                          content={msg.content}
                          msgId={msg.id}
                          claims={msg.claims}
                          onCitationClick={(idx) => scrollToEvidence(idx, msg.id)}
                        />
                      ) : (
                        <p className="whitespace-pre-wrap">{msg.content}</p>
                      )}

                      {/* Summary Cited Sources List (NotebookLM style) */}
                      {msg.role === "assistant" && msg.evidence && msg.evidence.length > 0 && (
                        <div className="mt-4 pt-3.5 border-t border-slate-800/80 flex flex-wrap gap-2 items-center text-[10px] text-slate-400">
                          <span className="font-bold uppercase tracking-wider text-[8px] mr-1">Sources Cited:</span>
                          {msg.evidence.map((ev, idx) => {
                            const name = getDocFilename(ev.document_id || "");
                            return (
                              <button
                                key={idx}
                                onClick={() => scrollToEvidence(idx + 1, msg.id)}
                                className="flex items-center gap-1 bg-slate-950/60 hover:bg-slate-950 border border-slate-800 hover:border-primary/50 text-slate-300 rounded px-2.5 py-0.5 transition-all text-[9px] font-semibold cursor-pointer shadow-sm"
                              >
                                <span className="font-bold text-primary mr-0.5">[{idx + 1}]</span>
                                <span className="truncate max-w-[110px]">{name}</span>
                                <span className="text-[8px] text-slate-500">(p. {ev.page_number || 1})</span>
                              </button>
                            );
                          })}
                        </div>
                      )}

                      {/* Verification Panel & Citations in System responses */}
                      {msg.role === "assistant" && !msg.loading && (
                        <div className="mt-4.5 space-y-4.5">
                          <VerificationPanel
                            grounded={msg.grounded ?? false}
                            confidence={msg.confidence ?? 0}
                            groundingScore={msg.groundingScore ?? 0}
                            evidenceScore={msg.evidenceScore ?? 0}
                            verificationReason={msg.verificationReason ?? ""}
                          />
                          <EvidencePanel
                            evidence={msg.evidence ?? []}
                            groundingScore={msg.groundingScore}
                            evidenceScore={msg.evidenceScore}
                            latencyMs={msg.latencyMs}
                            searchTimeMs={msg.searchTimeMs}
                            rerankTimeMs={msg.rerankTimeMs}
                            verificationReason={msg.verificationReason}
                            query={messages.find((m, idx) => messages[idx + 1]?.id === msg.id)?.content || ""}
                            msgId={msg.id}
                            // Expose detailed diagnostic latencies
                            retrievalTimeMs={msg.retrievalTimeMs}
                            generationTimeMs={msg.generationTimeMs}
                            verificationTimeMs={msg.verificationTimeMs}
                            embeddingModel={msg.embeddingModel}
                            llmModel={msg.llmModel}
                            semanticSimilarity={msg.semanticSimilarity}
                            lexicalOverlap={msg.lexicalOverlap}
                            consensusScore={msg.consensusScore}
                            selfCorrectionTriggered={msg.selfCorrectionTriggered}
                            refinementTimeMs={msg.refinementTimeMs}
                            conflicts={msg.conflicts}
                          />
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}

              {/* RAG Pipeline Visualizer (6 stages) */}
              {isLoading && (
                <div className="flex gap-4 items-start animate-fade-in">
                  <div className="flex-shrink-0">
                    <div className="w-7 h-7 rounded-xl bg-slate-900 border border-slate-850 text-primary flex items-center justify-center shadow-md animate-pulse">
                      <Shield className="w-4 h-4" />
                    </div>
                  </div>

                  <div className="flex-1 min-w-0 max-w-[85%] space-y-1">
                    <div className="flex items-center gap-2 text-[10px] font-bold text-slate-500">
                      <span>SYSTEM</span>
                      <span>•</span>
                      <span className="font-mono text-[9px]">processing...</span>
                    </div>

                    <div className="w-full max-w-md bg-slate-900 border border-slate-805/85 p-5 rounded-2xl shadow-xl space-y-4">
                      <div className="flex items-center justify-between border-b border-slate-800 pb-3.5">
                        <div className="flex items-center gap-2">
                          <Loader2 className="w-4 h-4 animate-spin text-primary" />
                          <span className="text-xs font-bold text-slate-200">Running Query Pipeline</span>
                        </div>
                        <span className="text-[10px] text-slate-400 font-mono">
                          Step {loadingStep + 1} of {PIPELINE_STEPS.length}
                        </span>
                      </div>

                      <div className="space-y-3.5">
                        {PIPELINE_STEPS.map((step, idx) => {
                          const isDone = loadingStep > idx;
                          const isActive = loadingStep === idx;

                          return (
                            <div key={idx} className="flex items-start gap-3 transition-opacity duration-200">
                              <div className="mt-0.5 flex-shrink-0">
                                {isDone ? (
                                  <div className="w-4.5 h-4.5 rounded-full bg-emerald-500/10 text-emerald-400 flex items-center justify-center border border-emerald-500/30">
                                    <CheckCircle2 className="w-3 h-3" />
                                  </div>
                                ) : isActive ? (
                                  <div className="w-4.5 h-4.5 rounded-full border border-primary flex items-center justify-center">
                                    <div className="w-2 h-2 bg-primary rounded-full animate-ping" />
                                  </div>
                                ) : (
                                  <div className="w-4.5 h-4.5 rounded-full border border-slate-800 flex items-center justify-center" />
                                )}
                              </div>
                              <div className="min-w-0">
                                <p className={`text-xs font-semibold ${isActive ? "text-primary" : isDone ? "text-slate-200" : "text-slate-500"}`}>
                                  {step.label}
                                </p>
                                {isActive && (
                                  <p className="text-[10px] text-slate-400 mt-0.5 leading-normal animate-pulse">
                                    {step.desc}
                                  </p>
                                )}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Info label if document limit filter active */}
        {selectedDocIds.length === 0 && (
          <div className="mx-6 px-4 py-2.5 bg-amber-500/5 border border-amber-500/25 rounded-xl text-[10px] text-amber-200 flex items-center gap-2 mb-2 animate-pulse">
            <Info className="w-4 h-4 text-amber-400 flex-shrink-0" />
            <span>
              <strong>Scoping Search Warning:</strong> No files are currently checked in your search scope. Natural language retrieval will yield 0 hits.
            </span>
          </div>
        )}

        <ChatInput onSend={handleSend} disabled={isLoading} />
      </div>

      {/* Document Search Scoping panel */}
      {user && (
        <DocumentSelector
          userId={user.uid}
          selectedIds={selectedDocIds}
          onChange={setSelectedDocIds}
        />
      )}
    </div>
  );
}

export default function ChatPage() {
  return (
    <Suspense fallback={
      <div className="h-screen flex items-center justify-center bg-slate-950 text-white">
        <Loader2 className="w-7 h-7 animate-spin text-primary" />
      </div>
    }>
      <ChatContent />
    </Suspense>
  );
}