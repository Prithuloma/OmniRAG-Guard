export default function DashboardPage() {
    return (
      <div className="p-8">
        <h1 className="text-2xl font-semibold mb-1">Dashboard</h1>
        <p className="text-muted-foreground text-sm mb-8">System overview and metrics</p>
        <div className="grid grid-cols-3 gap-4">
          {[
            { label: "Documents Indexed", value: "0" },
            { label: "Queries Processed", value: "0" },
            { label: "Hallucinations Caught", value: "0" },
          ].map((stat) => (
            <div key={stat.label} className="rounded-lg border border-border bg-card p-6">
              <p className="text-muted-foreground text-sm">{stat.label}</p>
              <p className="text-3xl font-semibold mt-2">{stat.value}</p>
            </div>
          ))}
        </div>
      </div>
    );
  }