"use client";

import { useState } from "react";
import { ShieldCheck, AlertTriangle, AlertCircle, ChevronDown, ChevronUp, BarChart2, Info } from "lucide-react";

interface VerificationPanelProps {
  grounded: boolean;
  confidence: number;       // Final blended confidence, 0-100
  groundingScore: number;   // Generation grounding index, 0-100
  evidenceScore: number;    // Lexical evidence score, 0-100
  verificationReason: string;
}

export default function VerificationPanel({
  grounded,
  confidence,
  groundingScore,
  evidenceScore,
  verificationReason,
}: VerificationPanelProps) {
  const [isOpen, setIsOpen] = useState(false);

  // Status mapping
  let status: "grounded" | "partial" | "low" = "low";
  if (grounded || confidence >= 75) {
    status = "grounded";
  } else if (confidence >= 40) {
    status = "partial";
  }

  const statusConfig = {
    grounded: {
      label: "Grounded Answer",
      textColor: "text-emerald-400",
      bgColor: "bg-emerald-500/10",
      borderColor: "border-emerald-500/20",
      icon: ShieldCheck,
      desc: "This response is strongly supported by the cited document source material.",
      barColor: "bg-emerald-500",
    },
    partial: {
      label: "Partially Grounded",
      textColor: "text-amber-400",
      bgColor: "bg-amber-500/10",
      borderColor: "border-amber-500/20",
      icon: AlertTriangle,
      desc: "This response aligns with source context but includes some unverified assertions or low similarity chunks.",
      barColor: "bg-amber-500",
    },
    low: {
      label: "Low Evidence",
      textColor: "text-red-400",
      bgColor: "bg-red-500/10",
      borderColor: "border-red-500/20",
      icon: AlertCircle,
      desc: "This response has weak lexical support in the retrieved documents. Verify facts independently.",
      barColor: "bg-red-500",
    },
  };

  const current = statusConfig[status];
  const Icon = current.icon;

  const barStyle = (score: number) => {
    let color = "bg-red-500";
    if (score >= 75) color = "bg-emerald-500";
    else if (score >= 40) color = "bg-amber-500";
    return color;
  };

  return (
    <div className={`rounded-xl border ${current.borderColor} ${current.bgColor} p-4 mt-3 transition-all duration-300 font-sans`}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3 min-w-0">
          <div className={`p-1.5 rounded-lg bg-slate-900 border ${current.borderColor} ${current.textColor} flex-shrink-0 mt-0.5`}>
            <Icon className="w-4 h-4" />
          </div>
          <div className="min-w-0">
            <h4 className={`text-xs font-bold uppercase tracking-wider ${current.textColor}`}>
              {current.label}
            </h4>
            <p className="text-[11px] text-muted-foreground/85 mt-0.5 leading-relaxed">
              {current.desc}
            </p>
          </div>
        </div>

        <button
          onClick={() => setIsOpen(!isOpen)}
          className="text-muted-foreground hover:text-foreground p-1 hover:bg-slate-900 rounded-lg transition-all flex-shrink-0 cursor-pointer"
        >
          {isOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
      </div>

      {isOpen && (
        <div className="mt-4 pt-4 border-t border-border/40 space-y-4 animate-fade-in">
          {/* Details breakdown */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {/* Blended Confidence */}
            <div className="bg-slate-950/45 border border-border/40 p-3 rounded-lg flex flex-col gap-1.5">
              <span className="text-[9px] uppercase font-bold text-muted-foreground/60 tracking-wider">
                Final Confidence
              </span>
              <div className="flex items-center justify-between text-xs font-semibold">
                <span>Blended Score</span>
                <span className={status === "grounded" ? "text-emerald-400" : status === "partial" ? "text-amber-400" : "text-red-400"}>
                  {confidence}%
                </span>
              </div>
              <div className="h-1.5 rounded-full bg-slate-900 overflow-hidden mt-1">
                <div
                  className={`h-full ${current.barColor} rounded-full transition-all duration-500`}
                  style={{ width: `${confidence}%` }}
                />
              </div>
            </div>

            {/* Grounding Score */}
            <div className="bg-slate-950/45 border border-border/40 p-3 rounded-lg flex flex-col gap-1.5">
              <span className="text-[9px] uppercase font-bold text-muted-foreground/60 tracking-wider">
                Generation Confidence
              </span>
              <div className="flex items-center justify-between text-xs font-semibold">
                <span>Semantic Sync</span>
                <span>{groundingScore}%</span>
              </div>
              <div className="h-1.5 rounded-full bg-slate-900 overflow-hidden mt-1">
                <div
                  className={`h-full ${barStyle(groundingScore)} rounded-full transition-all duration-500`}
                  style={{ width: `${groundingScore}%` }}
                />
              </div>
            </div>

            {/* Evidence Score */}
            <div className="bg-slate-950/45 border border-border/40 p-3 rounded-lg flex flex-col gap-1.5">
              <span className="text-[9px] uppercase font-bold text-muted-foreground/60 tracking-wider">
                Evidence Score
              </span>
              <div className="flex items-center justify-between text-xs font-semibold">
                <span>Lexical Overlap</span>
                <span>{evidenceScore}%</span>
              </div>
              <div className="h-1.5 rounded-full bg-slate-900 overflow-hidden mt-1">
                <div
                  className={`h-full ${barStyle(evidenceScore)} rounded-full transition-all duration-500`}
                  style={{ width: `${evidenceScore}%` }}
                />
              </div>
            </div>
          </div>

          {/* Reasoning */}
          {verificationReason && (
            <div className="p-3 bg-slate-950/30 border border-border/30 rounded-lg text-xs leading-relaxed text-muted-foreground">
              <div className="flex items-center gap-1.5 font-semibold text-foreground mb-1.5 uppercase text-[9px] tracking-wider">
                <Info className="w-3.5 h-3.5 text-primary" />
                <span>Verification Reasoning</span>
              </div>
              <p>{verificationReason}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
