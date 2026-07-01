interface Props {
  score: number; // 0 to 100
}

export default function ConfidenceBar({ score }: Props) {
  // Premium HSL values matching professional dark mode designs
  const color =
    score >= 75
      ? "hsl(142, 76%, 36%)" // Emerald green
      : score >= 45
      ? "hsl(38, 92%, 50%)"  // Amber orange
      : "hsl(0, 84%, 60%)";   // Coral red

  const label =
    score >= 75 ? "High confidence" : score >= 45 ? "Medium confidence" : "Low confidence";

  return (
    <div style={{ width: "100%" }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
        <span style={{ fontSize: "12px", color: "var(--muted-foreground)" }}>{label}</span>
        <span style={{ fontSize: "12px", fontWeight: 600, color }}>{score}%</span>
      </div>
      <div style={{ height: "6px", borderRadius: "9999px", background: "var(--border)", overflow: "hidden" }}>
        <div
          style={{
            height: "100%",
            width: `${score}%`,
            background: color,
            borderRadius: "9999px",
            transition: "width 0.6s cubic-bezier(0.16, 1, 0.3, 1)",
            boxShadow: `0 0 8px ${color}40`,
          }}
        />
      </div>
    </div>
  );
} 