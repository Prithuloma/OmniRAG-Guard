"use client";

import { useState } from "react";
import ChatInput from "@/components/chat/ChatInput";
import ConfidenceBar from "@/components/ui/ConfidenceBar";
import HallucinationBadge from "@/components/ui/HallucinationBadge";
import EvidencePanel from "@/components/ui/EvidencePanel";
import { queryRAG } from "@/services/api";

interface Evidence {
  id: string;
  source: string;
  chunk: string;
  relevance: number;
}

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  confidence?: number;
  grounded?: boolean;
  evidence?: Evidence[];
  loading?: boolean;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);

  const handleSend = async (content: string) => {
    const userMsg: Message = { id: Date.now().toString(), role: "user", content };
    const loadingMsg: Message = { id: (Date.now() + 1).toString(), role: "assistant", content: "Thinking...", loading: true };

    setMessages((prev) => [...prev, userMsg, loadingMsg]);

    try {
      const data = await queryRAG(content);

      const evidence: Evidence[] = (data.retrieved_chunks ?? []).map((c: any) => ({
        id: c.chunk_id,
        source: `${c.document_id} — page ${c.page_number}`,
        chunk: c.text,
        relevance: Math.round(c.score * 100),
      }));

      const botMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.answer ?? "No answer returned.",
        confidence: Math.round((data.confidence ?? 0) * 100),
        grounded: data.grounded,
        evidence,
      };

      setMessages((prev) => [...prev.slice(0, -1), botMsg]);
    } catch (err: any) {
      const errMsg = err.message || "Error connecting to backend.";
      setMessages((prev) => [
        ...prev.slice(0, -1),
        { id: Date.now().toString(), role: "assistant", content: errMsg, confidence: 0, grounded: false, evidence: [] },
      ]);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh" }}>
      <div className="p-6 border-b border-border">
        <h1 className="text-2xl font-semibold mb-1">Chat</h1>
        <p className="text-muted-foreground text-sm">Query your documents with RAG</p>
      </div>

      <div style={{ flex: 1, overflowY: "auto", padding: "1.5rem", display: "flex", flexDirection: "column", gap: "1rem" }}>
        {messages.length === 0 ? (
          <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <p className="text-muted-foreground text-sm">Ask anything about your uploaded documents</p>
          </div>
        ) : (
          messages.map((msg) => (
            <div key={msg.id} style={{ display: "flex", justifyContent: msg.role === "user" ? "flex-end" : "flex-start" }}>
              <div
                className={`rounded-lg px-4 py-3 text-sm ${msg.role === "user" ? "bg-primary text-primary-foreground" : "bg-card border border-border"}`}
                style={{ maxWidth: "70%" }}
              >
                <p className="mb-3">{msg.content}</p>
                {msg.role === "assistant" && !msg.loading && (
                  <div style={{ display: "flex", flexDirection: "column", gap: "8px", marginTop: "8px" }}>
                    <ConfidenceBar score={msg.confidence ?? 0} />
                    <HallucinationBadge detected={!msg.grounded} />
                    <EvidencePanel evidence={msg.evidence ?? []} />
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      <ChatInput onSend={handleSend} />
    </div>
  );
}