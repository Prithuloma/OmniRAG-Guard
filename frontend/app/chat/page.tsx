"use client";

import { useState } from "react";
import ChatInput from "@/components/chat/ChatInput";
import ConfidenceBar from "@/components/ui/ConfidenceBar";
import HallucinationBadge from "@/components/ui/HallucinationBadge";
import EvidencePanel from "@/components/ui/EvidencePanel";

interface Message {
    id: string;
    role: "user" | "assistant";
    content: string;
    evidence?: { id: string; source: string; chunk: string; relevance: number }[];
  }

export default function ChatPage() {
    const [messages, setMessages] = useState<Message[]>([]);

    const handleSend = (content: string) => {
        const userMsg: Message = { id: Date.now().toString(), role: "user", content };
        const botMsg: Message = {
            id: (Date.now() + 1).toString(),
            role: "assistant",
            content: "Backend not connected yet. This is a placeholder response.",
            evidence: [
              { id: "1", source: "document.pdf — page 3", chunk: "The system uses adaptive retrieval to verify responses against indexed sources.", relevance: 91 },
              { id: "2", source: "report.pdf — page 7", chunk: "Hallucination detection is performed using semantic similarity scoring.", relevance: 78 },
            ],
          };
        setMessages((prev) => [...prev, userMsg, botMsg]);
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
                        <div
                            key={msg.id}
                            style={{ display: "flex", justifyContent: msg.role === "user" ? "flex-end" : "flex-start" }}
                        >
                            <div
                                className={`rounded-lg px-4 py-3 text-sm ${msg.role === "user" ? "bg-primary text-primary-foreground" : "bg-card border border-border"}`}
                                style={{ maxWidth: "70%" }}
                            >
                                <p className="mb-3">{msg.content}</p>
                                {msg.role === "assistant" && (
                                    <div style={{ display: "flex", flexDirection: "column", gap: "8px", marginTop: "8px" }}>
                                        <ConfidenceBar score={72} />
                                        <HallucinationBadge detected={false} />
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