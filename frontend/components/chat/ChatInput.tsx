"use client";

import { useState, useRef, useEffect } from "react";
import { Send } from "lucide-react";

interface Props {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export default function ChatInput({ onSend, disabled }: Props) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-grow textarea effect
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = `${Math.min(textarea.scrollHeight, 180)}px`;
    }
  }, [value]);

  const handleSend = () => {
    if (!value.trim() || disabled) return;
    onSend(value.trim());
    setValue("");
  };

  return (
    <div className="flex items-end gap-3 p-4 border-t border-border bg-slate-950 font-sans">
      <div className="relative flex-1 flex items-center bg-slate-900/60 border border-border/80 focus-within:border-primary/50 focus-within:ring-1 focus-within:ring-primary/20 rounded-xl transition-all p-1">
        <textarea
          ref={textareaRef}
          className="w-full bg-transparent border-0 text-white px-3.5 py-2.5 text-xs outline-none resize-none min-h-[40px] max-h-[180px] placeholder:text-muted-foreground/45"
          placeholder="Ask a question about your workspace documents..."
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
          rows={1}
          disabled={disabled}
        />
      </div>
      <button
        onClick={handleSend}
        disabled={disabled || !value.trim()}
        className="rounded-xl bg-primary text-primary-foreground p-3.5 hover:opacity-95 shadow-md shadow-primary/10 transition-all cursor-pointer flex-shrink-0 disabled:opacity-40 disabled:cursor-not-allowed"
      >
        <Send className="w-3.5 h-3.5" />
      </button>
    </div>
  );
}