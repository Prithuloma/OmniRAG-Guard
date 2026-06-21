import Link from "next/link";
import { Shield, ArrowRight, Zap, ShieldCheck, FileText } from "lucide-react";

export default function Home() {
  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "2rem", position: "relative" }}>

      {/* Center glow */}
      <div style={{
        position: "absolute",
        width: "600px", height: "600px",
        borderRadius: "50%",
        background: "radial-gradient(circle, rgba(139, 92, 246, 0.12) 0%, transparent 70%)",
        pointerEvents: "none",
      }} />

      {/* Badge */}
      <div style={{
        display: "inline-flex", alignItems: "center", gap: "8px",
        padding: "6px 16px", borderRadius: "9999px",
        border: "1px solid rgba(139, 92, 246, 0.4)",
        background: "rgba(139, 92, 246, 0.1)",
        marginBottom: "2rem",
      }}>
        <div style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#a78bfa", boxShadow: "0 0 6px #a78bfa" }} />
        <span style={{ fontSize: "12px", color: "#a78bfa", fontWeight: 500 }}>Adaptive Multi-Modal RAG System</span>
      </div>

      {/* Title */}
      <h1 style={{
        fontSize: "clamp(2.5rem, 6vw, 5rem)",
        fontWeight: 700,
        textAlign: "center",
        marginBottom: "1.5rem",
        lineHeight: 1.1,
        background: "linear-gradient(135deg, #ffffff 0%, #a78bfa 50%, #7c3aed 100%)",
        WebkitBackgroundClip: "text",
        WebkitTextFillColor: "transparent",
        backgroundClip: "text",
      }}>
        OmniRAG-Guard
      </h1>

      {/* Subtitle */}
      <p style={{
        fontSize: "clamp(1rem, 2vw, 1.25rem)",
        color: "rgba(167, 139, 250, 0.7)",
        textAlign: "center",
        maxWidth: "560px",
        lineHeight: 1.7,
        marginBottom: "3rem",
      }}>
        Hallucination verification, semantic evidence checking, and adaptive model routing — all in one platform.
      </p>

      {/* Buttons */}
      <div style={{ display: "flex", gap: "1rem", marginBottom: "4rem", flexWrap: "wrap", justifyContent: "center" }}>
        <Link href="/chat" style={{
          display: "inline-flex", alignItems: "center", gap: "8px",
          padding: "12px 28px", borderRadius: "8px",
          background: "linear-gradient(135deg, #7c3aed, #a78bfa)",
          color: "#fff", fontWeight: 600, fontSize: "14px",
          textDecoration: "none",
          boxShadow: "0 0 20px rgba(139, 92, 246, 0.4), 0 0 40px rgba(139, 92, 246, 0.2)",
        }}>
          Start Querying <ArrowRight style={{ width: "16px", height: "16px" }} />
        </Link>
        <Link href="/upload" style={{
          display: "inline-flex", alignItems: "center", gap: "8px",
          padding: "12px 28px", borderRadius: "8px",
          border: "1px solid rgba(139, 92, 246, 0.4)",
          background: "rgba(139, 92, 246, 0.08)",
          color: "#a78bfa", fontWeight: 600, fontSize: "14px",
          textDecoration: "none",
        }}>
          Upload Documents
        </Link>
      </div>

      {/* Feature pills */}
      <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap", justifyContent: "center" }}>
        {[
          { icon: ShieldCheck, label: "Hallucination Detection" },
          { icon: Zap, label: "Confidence Scoring" },
          { icon: FileText, label: "Multi-Modal RAG" },
          { icon: Shield, label: "Evidence Verification" },
        ].map(({ icon: Icon, label }) => (
          <div key={label} style={{
            display: "inline-flex", alignItems: "center", gap: "8px",
            padding: "8px 16px", borderRadius: "8px",
            border: "1px solid rgba(139, 92, 246, 0.2)",
            background: "rgba(15, 10, 30, 0.6)",
            backdropFilter: "blur(8px)",
          }}>
            <Icon style={{ width: "14px", height: "14px", color: "#a78bfa" }} />
            <span style={{ fontSize: "12px", color: "rgba(200, 195, 255, 0.7)" }}>{label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}