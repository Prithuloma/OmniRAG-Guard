import { FileText, MessageSquare, ShieldCheck, Zap } from "lucide-react";

const stats = [
  { label: "Documents Indexed", value: "0", icon: FileText, desc: "PDFs, images, tables" },
  { label: "Queries Processed", value: "0", icon: MessageSquare, desc: "Total RAG queries" },
  { label: "Hallucinations Caught", value: "0", icon: ShieldCheck, desc: "Verified and flagged" },
  { label: "Avg Confidence", value: "—", icon: Zap, desc: "Across all responses" },
];

export default function DashboardPage() {
  return (
    <div style={{ padding: "2rem" }}>
      <h1 style={{ fontSize: "1.5rem", fontWeight: 600, marginBottom: "4px" }}>Dashboard</h1>
      <p style={{ color: "rgba(167, 139, 250, 0.6)", fontSize: "13px", marginBottom: "2rem" }}>
        System overview and pipeline metrics
      </p>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "1rem", marginBottom: "2rem" }}>
        {stats.map(({ label, value, icon: Icon, desc }) => (
          <div key={label} style={{
            borderRadius: "12px",
            border: "1px solid rgba(139, 92, 246, 0.25)",
            background: "rgba(15, 10, 30, 0.7)",
            backdropFilter: "blur(12px)",
            padding: "1.5rem",
            position: "relative",
            overflow: "hidden",
            boxShadow: "0 0 20px rgba(139, 92, 246, 0.08), inset 0 0 20px rgba(139, 92, 246, 0.03)",
          }}>
            {/* Top glow */}
            <div style={{
              position: "absolute", top: 0, left: 0, right: 0, height: "1px",
              background: "linear-gradient(90deg, transparent, rgba(139, 92, 246, 0.6), transparent)",
            }} />

            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
              <p style={{ fontSize: "11px", color: "rgba(167, 139, 250, 0.6)" }}>{label}</p>
              <Icon style={{ width: "16px", height: "16px", color: "rgba(139, 92, 246, 0.7)" }} />
            </div>
            <p style={{ fontSize: "2rem", fontWeight: 600, marginBottom: "8px", color: "#e2e0ff" }}>{value}</p>
            <p style={{ fontSize: "11px", color: "rgba(167, 139, 250, 0.4)" }}>{desc}</p>
          </div>
        ))}
      </div>

      {/* Recent Activity */}
      <div style={{
        borderRadius: "12px",
        border: "1px solid rgba(139, 92, 246, 0.25)",
        background: "rgba(15, 10, 30, 0.7)",
        backdropFilter: "blur(12px)",
        padding: "1.5rem",
        position: "relative",
        overflow: "hidden",
        boxShadow: "0 0 20px rgba(139, 92, 246, 0.08)",
      }}>
        <div style={{
          position: "absolute", top: 0, left: 0, right: 0, height: "1px",
          background: "linear-gradient(90deg, transparent, rgba(139, 92, 246, 0.6), transparent)",
        }} />
        <h2 style={{ fontSize: "13px", fontWeight: 500, marginBottom: "1.5rem", color: "#e2e0ff" }}>Recent Activity</h2>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100px" }}>
          <p style={{ fontSize: "13px", color: "rgba(167, 139, 250, 0.4)" }}>
            No activity yet — upload a document to get started
          </p>
        </div>
      </div>
    </div>
  );
}