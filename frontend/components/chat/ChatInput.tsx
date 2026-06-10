"use client";

import { useState } from "react";
import { Send } from "lucide-react";

interface Props {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export default function ChatInput({ onSend, disabled }: Props) {
  const [value, setValue] = useState("");

  const handleSend = () => {
    if (!value.trim()) return;
    onSend(value.trim());
    setValue("");
  };

  return (
    <div className="flex items-end gap-3 p-4 border-t border-border bg-card">
      <textarea
        className="flex-1 resize-none rounded-lg border border-border bg-background px-4 py-3 text-sm outline-none focus:ring-1 focus:ring-ring min-h-[52px] max-h-[160px]"
        placeholder="Ask a question about your documents..."
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
          }
        }}
        rows={1}
      />
      <button
        onClick={handleSend}
        disabled={disabled || !value.trim()}
        className="rounded-lg bg-primary text-primary-foreground p-3 hover:opacity-90 disabled:opacity-40 transition-opacity"
      >
        <Send className="w-4 h-4" />
      </button>
    </div>
  );
}