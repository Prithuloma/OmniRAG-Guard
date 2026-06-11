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
  Evidence
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
  Database
} from "lucide-react";

// Visualizer steps for pipeline
const PIPELINE_STEPS = [
  { label: "Retrieving Context", desc: "Searching Qdrant vector database" },
  { label: "Reranking Passages", desc: "Cross-encoder relevancy check" },
  { label: "Generating Response", desc: "Synthesizing reply via LLM model" },
  { label: "Verifying Evidence", desc: "Hallucination alignment assessment" },
  { label: "Finalizing Answer", desc: "Query verification complete" },
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

function ChatContent() {
  const { user } = useAuth();
  const searchParams = useSearchParams();
  const router = useRouter();
  const activeChatId = searchParams.get("id");

  const [messages, setMessages] = useState<Message[]>([]);
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const [loadingStep, setLoadingStep] = useState(0);
  const [isLoading, setIsLoading] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const loadingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Initialize selected document IDs to match the user's history files by default
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
    }, 900);

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

            // Save conversation state
            const currentConv: Conversation = {
              id: chatId,
              title: chatTitle || getConversations(user.uid).find((c) => c.id === chatId)?.title || "Untitled Chat",
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
      }, 15);

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
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col h-full overflow-hidden relative">
        {/* Chat header */}
        <div className="p-4 border-b border-border bg-slate-900/20 backdrop-blur flex items-center justify-between flex-shrink-0 z-10">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 text-primary border border-primary/10 rounded-xl">
              <Shield className="w-4 h-4" />
            </div>
            <div>
              <h1 className="text-xs font-bold uppercase tracking-wider text-slate-200">Secure Grounded QA</h1>
              <p className="text-[10px] text-muted-foreground mt-0.5 leading-none">
                Queries verify source alignment using mathematical consensus
              </p>
            </div>
          </div>
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
                <p className="text-[11px] text-muted-foreground leading-relaxed max-w-sm mx-auto">
                  OmniRAG-Guard uses semantic search, dense embedding maps, and hybrid consensus scoring to deliver evidence-backed assertions.
                </p>
              </div>

              {/* Starter Prompts */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full pt-4">
                {ONBOARDING_PROMPTS.map((prompt, i) => (
                  <button
                    key={i}
                    onClick={() => handleSend(prompt.text)}
                    className="p-3.5 text-left text-xs bg-slate-900/30 border border-border/80 rounded-xl hover:bg-slate-900/80 hover:border-primary/40 hover:shadow-lg transition-all duration-200 cursor-pointer flex justify-between items-center group"
                  >
                    <div className="min-w-0 pr-2">
                      <span className="font-semibold text-slate-200 block truncate">{prompt.text}</span>
                      <span className="text-[10px] text-muted-foreground/60 block mt-0.5 truncate">{prompt.desc}</span>
                    </div>
                    <ArrowRight className="w-3.5 h-3.5 text-muted-foreground group-hover:text-primary transition-colors flex-shrink-0" />
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
                      <div className="w-7 h-7 rounded-xl bg-slate-900 border border-border text-primary flex items-center justify-center shadow-md">
                        <Shield className="w-4 h-4" />
                      </div>
                    )}
                  </div>

                  {/* Bubble content */}
                  <div className="flex-1 min-w-0 max-w-[85%] space-y-1">
                    <div className={`flex items-center gap-2 text-[10px] font-bold text-muted-foreground/50 ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                      <span>{msg.role === "user" ? "YOU" : "SYSTEM"}</span>
                      <span>•</span>
                      <span className="font-mono text-[9px]">{msg.timestamp}</span>
                    </div>

                    <div
                      className={`rounded-2xl px-4.5 py-3.5 text-xs select-text leading-relaxed shadow-sm
                        ${
                          msg.role === "user"
                            ? "bg-primary text-primary-foreground font-medium rounded-tr-none ml-auto"
                            : "bg-slate-900/60 border border-border/70 text-slate-100 rounded-tl-none"
                        }`}
                    >
                      <p className="whitespace-pre-wrap">{msg.content}</p>

                      {/* Verification Panel & Citations in System responses */}
                      {msg.role === "assistant" && !msg.loading && (
                        <div className="mt-4 space-y-4">
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
                          />
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}

              {/* RAG Pipeline Visualizer */}
              {isLoading && (
                <div className="flex gap-4 items-start animate-fade-in">
                  <div className="flex-shrink-0">
                    <div className="w-7 h-7 rounded-xl bg-slate-900 border border-border text-primary flex items-center justify-center shadow-md animate-pulse">
                      <Shield className="w-4 h-4" />
                    </div>
                  </div>

                  <div className="flex-1 min-w-0 max-w-[85%] space-y-1">
                    <div className="flex items-center gap-2 text-[10px] font-bold text-muted-foreground/50">
                      <span>SYSTEM</span>
                      <span>•</span>
                      <span className="font-mono text-[9px]">processing...</span>
                    </div>

                    <div className="w-full max-w-md bg-slate-900 border border-border/80 p-5 rounded-2xl shadow-xl space-y-4">
                      <div className="flex items-center justify-between border-b border-border pb-3.5">
                        <div className="flex items-center gap-2">
                          <Loader2 className="w-4 h-4 animate-spin text-primary" />
                          <span className="text-xs font-bold text-slate-200">Running Query Pipeline</span>
                        </div>
                        <span className="text-[10px] text-muted-foreground font-mono">
                          Step {loadingStep + 1} of 5
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
                                  <div className="w-4.5 h-4.5 rounded-full border border-border/85 flex items-center justify-center" />
                                )}
                              </div>
                              <div className="min-w-0">
                                <p className={`text-xs font-semibold ${isActive ? "text-primary" : isDone ? "text-slate-200" : "text-muted-foreground/45"}`}>
                                  {step.label}
                                </p>
                                {isActive && (
                                  <p className="text-[10px] text-muted-foreground mt-0.5 leading-normal animate-pulse">
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