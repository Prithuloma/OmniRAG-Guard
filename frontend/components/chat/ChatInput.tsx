"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Mic } from "lucide-react";

interface Props {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export default function ChatInput({ onSend, disabled }: Props) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  
  // Voice feature states
  const [isListening, setIsListening] = useState(false);
  const [isSpeechSupported, setIsSpeechSupported] = useState(false);
  const recognitionRef = useRef<any>(null);

  // Initialize SpeechRecognition client-side
  useEffect(() => {
    if (typeof window !== "undefined") {
      const SpeechRecognition =
        (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SpeechRecognition) {
        setIsSpeechSupported(true);
        const rec = new SpeechRecognition();
        rec.continuous = false;
        rec.interimResults = false;
        rec.lang = "en-US";

        rec.onresult = (event: any) => {
          const transcript = event.results[0][0].transcript;
          setValue((prev) => (prev ? prev + " " + transcript : transcript));
        };

        rec.onerror = (event: any) => {
          console.error("Speech recognition error:", event.error);
          setIsListening(false);
        };

        rec.onend = () => {
          setIsListening(false);
        };

        recognitionRef.current = rec;
      }
    }
  }, []);

  const toggleListening = () => {
    if (!recognitionRef.current || disabled) return;

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      try {
        recognitionRef.current.start();
        setIsListening(true);
      } catch (err) {
        console.error("Failed to start speech recognition:", err);
      }
    }
  };

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
    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
    }
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
      
      {isSpeechSupported && (
        <button
          onClick={toggleListening}
          disabled={disabled}
          className={`rounded-xl p-3.5 border transition-all cursor-pointer flex-shrink-0 disabled:opacity-40 disabled:cursor-not-allowed
            ${isListening 
              ? "bg-red-500/10 border-red-500/30 text-red-400 animate-pulse scale-105 shadow-inner shadow-red-500/5" 
              : "bg-slate-900 border-border/80 text-slate-400 hover:text-white hover:border-border hover:bg-slate-900/80"
            }`}
          title={isListening ? "Stop voice listening" : "Record voice query"}
        >
          <Mic className="w-3.5 h-3.5" />
        </button>
      )}

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