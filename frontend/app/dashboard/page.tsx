"use client";

import { useAuth } from "@/context/AuthContext";
import { getHistory } from "@/lib/history";
import { useEffect, useState } from "react";
import { FileText, MessageSquare, ShieldCheck, Zap, ArrowUpRight } from "lucide-react";
import Link from "next/link";

export default function DashboardPage() {
  const { user } = useAuth();
  const [docCount, setDocCount] = useState(0);
  const [recentFiles, setRecentFiles] = useState<any[]>([]);

  useEffect(() => {
    if (user) {
      const history = getHistory(user.uid);
      setDocCount(history.length);
      setRecentFiles(history.slice(0, 3));
    }
  }, [user]);

  const stats = [
    { label: "Documents Indexed", value: docCount.toString(), icon: FileText, desc: "PDFs, images, tables" },
    { label: "Queries Processed", value: "0", icon: MessageSquare, desc: "Total RAG queries" },
    { label: "Hallucinations Caught", value: "0", icon: ShieldCheck, desc: "Verified and flagged" },
    { label: "Avg Confidence", value: "—", icon: Zap, desc: "Across all responses" },
  ];

  return (
    <div className="p-8 font-sans">
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
        {recentFiles.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-32 gap-3">
            <p className="text-muted-foreground text-sm">No activity yet — upload a document to get started</p>
            <Link
              href="/upload"
              className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
            >
              <span>Go to Upload</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        ) : (
          <div className="divide-y divide-border">
            {recentFiles.map((file) => (
              <div key={file.documentId} className="py-3 flex items-center justify-between first:pt-0 last:pb-0">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded bg-primary/10 text-primary">
                    <FileText className="w-4 h-4" />
                  </div>
                  <div>
                    <p className="text-sm font-medium">{file.filename}</p>
                    <p className="text-xs text-muted-foreground font-mono">ID: {file.documentId}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-xs font-medium">{file.size}</p>
                  <p className="text-[10px] text-muted-foreground">
                    {new Date(file.uploadDate).toLocaleDateString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}