interface Props {
    score: number; // 0 to 100
  }
  
  export default function ConfidenceBar({ score }: Props) {
    const color =
      score >= 75 ? "#22c55e" : score >= 45 ? "#f59e0b" : "#ef4444";
  
    const label =
      score >= 75 ? "High confidence" : score >= 45 ? "Medium confidence" : "Low confidence";
  
    return (
      <div style={{ width: "100%" }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
          <span style={{ fontSize: "12px", color: "var(--muted-foreground)" }}>{label}</span>
          <span style={{ fontSize: "12px", fontWeight: 500, color }}>{score}%</span>
        </div>
        <div style={{ height: "6px", borderRadius: "9999px", background: "var(--border)", overflow: "hidden" }}>
          <div style={{
            height: "100%",
            width: `${score}%`,
            background: color,
            borderRadius: "9999px",
            transition: "width 0.5s ease",
          }} />
        </div>
      </div>
    );
  } 