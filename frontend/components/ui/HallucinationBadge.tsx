interface Props {
    detected: boolean;
  }
  
  export default function HallucinationBadge({ detected }: Props) {
    if (!detected) {
      return (
        <div style={{ display: "inline-flex", alignItems: "center", gap: "6px", padding: "4px 10px", borderRadius: "9999px", background: "#16a34a22", border: "1px solid #16a34a55" }}>
          <div style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#22c55e" }} />
          <span style={{ fontSize: "11px", color: "#22c55e", fontWeight: 500 }}>Verified</span>
        </div>
      );
    }
  
    return (
      <div style={{ display: "inline-flex", alignItems: "center", gap: "6px", padding: "4px 10px", borderRadius: "9999px", background: "#dc262622", border: "1px solid #dc262655" }}>
        <div style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#ef4444" }} />
        <span style={{ fontSize: "11px", color: "#ef4444", fontWeight: 500 }}>Hallucination detected</span>
      </div>
    );
  }