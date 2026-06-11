"use client";

import { Shield, Sparkles, Database, Layers, CheckCircle2, ArrowRight, Activity, Terminal } from "lucide-react";
import Link from "next/link";

export default function Home() {
  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans overflow-hidden relative">
      {/* Glow backgrounds */}
      <div className="absolute top-[-25%] left-[-20%] w-[900px] h-[900px] rounded-full bg-violet-950/15 blur-[170px] pointer-events-none" />
      <div className="absolute bottom-[-25%] right-[-20%] w-[900px] h-[900px] rounded-full bg-indigo-950/15 blur-[170px] pointer-events-none" />

      {/* Header Bar */}
      <header className="w-full px-8 py-5 border-b border-border/40 backdrop-blur flex items-center justify-between z-10">
        <div className="flex items-center gap-2.5">
          <div className="p-2 bg-primary/10 border border-primary/20 text-primary rounded-xl">
            <Shield className="w-4.5 h-4.5" />
          </div>
          <span className="font-bold text-xs uppercase tracking-wider text-white">OmniRAG-Guard</span>
        </div>
        
        <Link
          href="/dashboard"
          className="text-xs font-semibold text-primary hover:underline transition-all"
        >
          Go to App Dashboard
        </Link>
      </header>

      {/* Hero Section */}
      <div className="flex-1 max-w-4xl mx-auto px-6 py-16 text-center flex flex-col items-center justify-center space-y-8 z-10">
        {/* Badge */}
        <div className="inline-flex items-center gap-2 px-3 py-1 bg-slate-900 border border-border/60 rounded-full text-[10px] font-semibold text-slate-300 shadow">
          <Sparkles className="w-3.5 h-3.5 text-amber-400 fill-amber-400/20" />
          <span>Adaptive Hybrid Verification RAG</span>
        </div>

        {/* Title */}
        <div className="space-y-4">
          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white leading-tight">
            Trustworthy AI QA, <br />
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-primary via-indigo-400 to-slate-200">
              Mathematically Verified.
            </span>
          </h1>
          <p className="text-xs sm:text-sm text-muted-foreground max-w-lg mx-auto leading-relaxed">
            OmniRAG-Guard is a secure knowledge ingestion and search platform. We align LLM assertions with dense source documents using dual-phase semantic consensus scoring.
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex flex-col sm:flex-row gap-4 w-full justify-center max-w-xs sm:max-w-none pt-4">
          <Link
            href="/chat"
            className="inline-flex items-center justify-center gap-2 bg-primary text-primary-foreground font-semibold text-xs px-6 py-3.5 rounded-xl shadow-lg shadow-primary/15 hover:opacity-95 active:translate-y-px transition-all cursor-pointer"
          >
            <span>Launch Query Console</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
          <Link
            href="/upload"
            className="inline-flex items-center justify-center gap-2 bg-slate-900 hover:bg-slate-800 text-slate-100 border border-border font-semibold text-xs px-6 py-3.5 rounded-xl hover:border-border/80 transition-all cursor-pointer"
          >
            <span>Upload & Index Files</span>
          </Link>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 pt-16 w-full text-left">
          {/* Card 1 */}
          <div className="rounded-2xl border border-border/70 bg-slate-900/30 p-5 space-y-3 shadow transition-all hover:border-border/90">
            <div className="p-2 bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 rounded-xl inline-flex">
              <Database className="w-4 h-4" />
            </div>
            <h3 className="font-semibold text-xs text-slate-200">Dense Vector Storage</h3>
            <p className="text-[10px] text-muted-foreground/80 leading-relaxed">
              Chunked document partitions are projected in vector space and stored in high-performance Qdrant indices for lightning search.
            </p>
          </div>

          {/* Card 2 */}
          <div className="rounded-2xl border border-border/70 bg-slate-900/30 p-5 space-y-3 shadow transition-all hover:border-border/90">
            <div className="p-2 bg-violet-500/10 text-violet-400 border border-violet-500/20 rounded-xl inline-flex">
              <Layers className="w-4 h-4" />
            </div>
            <h3 className="font-semibold text-xs text-slate-200">Cross-Encoder Reranking</h3>
            <p className="text-[10px] text-muted-foreground/80 leading-relaxed">
              Surfaced text segments undergo a secondary deep-learning cross-encoder evaluation to maximize contextual alignment before answering.
            </p>
          </div>

          {/* Card 3 */}
          <div className="rounded-2xl border border-border/70 bg-slate-900/30 p-5 space-y-3 shadow transition-all hover:border-border/90">
            <div className="p-2 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-xl inline-flex">
              <CheckCircle2 className="w-4 h-4" />
            </div>
            <h3 className="font-semibold text-xs text-slate-200">Consensus Verification</h3>
            <p className="text-[10px] text-muted-foreground/80 leading-relaxed">
              Answers are cross-checked using dual lexical and semantic cosine matrices to automatically flag and suppress hallucinations.
            </p>
          </div>
        </div>

        {/* Stats segment */}
        <div className="pt-12 flex items-center justify-center gap-8 text-xs text-muted-foreground/60">
          <div className="flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-primary" />
            <span>Secure Enterprise Auth</span>
          </div>
          <span>•</span>
          <div className="flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-primary" />
            <span>Verified Citation Maps</span>
          </div>
          <span>•</span>
          <div className="flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-primary" />
            <span>Fast Ingestion Pipelines</span>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="w-full py-6 text-center border-t border-border/40 text-[10px] text-muted-foreground/50 bg-slate-950 z-10">
        © {new Date().getFullYear()} OmniRAG-Guard Inc. Secure, evidence-backed conversational context architectures.
      </footer>
    </main>
  );
}