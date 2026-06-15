"use client";

import { ShieldCheck, AlertTriangle, AlertCircle } from "lucide-react";

interface VerificationPanelProps {
  grounded: boolean;
  confidence: number;       // Blended confidence, 0-100
  groundingScore: number;   // Semantic Sync index, 0-100
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
  // Determine confidence threshold
  if (confidence >= 75) {
    return (
      <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[11px] font-semibold select-none shadow-sm shadow-emerald-500/5">
        <ShieldCheck className="w-3.5 h-3.5" />
        <span>Grounded Answer ({Math.round(confidence)}%)</span>
      </div>
    );
  } else if (confidence >= 45) {
    return (
      <div className="flex items-center gap-2 px-3.5 py-2.5 rounded-xl bg-amber-500/5 border border-amber-500/10 text-amber-400 text-xs select-none">
        <AlertTriangle className="w-4 h-4 flex-shrink-0 animate-pulse-subtle" />
        <span className="leading-relaxed font-medium">Some parts of this summary are based on limited evidence.</span>
      </div>
    );
  } else {
    return (
      <div className="flex items-center gap-2 px-3.5 py-2.5 rounded-xl bg-red-500/5 border border-red-500/10 text-red-400 text-xs select-none">
        <AlertCircle className="w-4 h-4 flex-shrink-0 animate-pulse-subtle" />
        <span className="leading-relaxed font-medium">This summary may contain unsupported information because the available evidence is limited.</span>
      </div>
    );
  }
}
