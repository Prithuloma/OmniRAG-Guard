import { FileText, MessageSquare, ShieldCheck, Zap } from "lucide-react";

const stats = [
  { label: "Documents Indexed", value: "0", icon: FileText, desc: "PDFs, images, tables" },
  { label: "Queries Processed", value: "0", icon: MessageSquare, desc: "Total RAG queries" },
  { label: "Hallucinations Caught", value: "0", icon: ShieldCheck, desc: "Verified and flagged" },
  { label: "Avg Confidence", value: "—", icon: Zap, desc: "Across all responses" },
];

export default function DashboardPage() {
  return (
    <div className="p-8">
      <h1 className="text-2xl font-semibold mb-1">Dashboard</h1>
      <p className="text-muted-foreground text-sm mb-8">System overview and pipeline metrics</p>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "1rem", marginBottom: "2rem" }}>
        {stats.map(({ label, value, icon: Icon, desc }) => (
          <div key={label} className="rounded-lg border border-border bg-card p-5">
            <div className="flex items-center justify-between mb-3">
              <p className="text-muted-foreground text-xs">{label}</p>
              <Icon className="w-4 h-4 text-muted-foreground" />
            </div>
            <p className="text-3xl font-semibold mb-2">{value}</p>
            <p className="text-xs text-muted-foreground">{desc}</p>
          </div>
        ))}
      </div>

      <div className="rounded-lg border border-border bg-card p-6">
        <h2 className="text-sm font-medium mb-4">Recent Activity</h2>
        <div className="flex items-center justify-center h-32">
          <p className="text-muted-foreground text-sm">No activity yet — upload a document to get started</p>
        </div>
      </div>
    </div>
  );
}