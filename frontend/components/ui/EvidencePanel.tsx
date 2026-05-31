interface Evidence {
    id: string;
    source: string;
    chunk: string;
    relevance: number;
  }
  
  interface Props {
    evidence: Evidence[];
  }
  
  export default function EvidencePanel({ evidence }: Props) {
    if (evidence.length === 0) return null;
  
    return (
      <div style={{ marginTop: "12px", borderTop: "1px solid var(--border)", paddingTop: "12px" }}>
        <p style={{ fontSize: "11px", color: "var(--muted-foreground)", marginBottom: "8px", fontWeight: 500 }}>
          Sources used
        </p>
        <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
          {evidence.map((e) => (
            <div key={e.id} style={{
              padding: "8px 12px",
              borderRadius: "8px",
              background: "var(--background)",
              border: "1px solid var(--border)",
            }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
                <span style={{ fontSize: "11px", fontWeight: 500 }}>{e.source}</span>
                <span style={{ fontSize: "11px", color: "#22c55e" }}>{e.relevance}% match</span>
              </div>
              <p style={{ fontSize: "11px", color: "var(--muted-foreground)", lineHeight: 1.5 }}>{e.chunk}</p>
            </div>
          ))}
        </div>
      </div>
    );
  }