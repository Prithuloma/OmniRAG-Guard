"use client";

import { useState } from "react";
import ChatInput from "@/components/chat/ChatInput";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);

  const handleSend = (content: string) => {
    const userMsg: Message = { id: Date.now().toString(), role: "user", content };
    const botMsg: Message = {
      id: (Date.now() + 1).toString(),
      role: "assistant",
      content: "Backend not connected yet. This is a placeholder response.",
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
                className={`rounded-lg px-4 py-3 text-sm max-w-[70%] ${
                  msg.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : "bg-card border border-border"
                }`}
              >
                {msg.content}
              </div>
            </div>
          ))
        )}
      </div>

      <ChatInput onSend={handleSend} />
    </div>
  );
}