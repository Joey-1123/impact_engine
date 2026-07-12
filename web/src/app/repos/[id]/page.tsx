import Link from "next/link";
import { getOverview, getHealthScore, getCosts, type OverviewResponse, type HealthScoreResponse } from "@/lib/api";

export default async function RepoPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  let overview: OverviewResponse | null = null;
  let health: HealthScoreResponse | null = null;
  let cost: { estimated_cost_usd: number } | null = null;

  try {
    [overview, health, cost] = await Promise.all([
      getOverview(id).catch(() => null),
      getHealthScore(id).catch(() => null),
      getCosts(id, "file_summary,tour_step", 10).catch(() => null),
    ]);
  } catch {}

  return (
    <div className="min-h-screen p-8">
      <header className="mb-8">
        <Link href="/" className="text-sm text-indigo-500 hover:underline mb-2 inline-block">&larr; Dashboard</Link>
        <h1 className="text-2xl font-bold">Repository: {id}</h1>
      </header>

      <nav className="flex gap-4 mb-8 border-b border-[var(--border)] pb-2">
        <Tab href={`/repos/${id}`} label="Overview" active />
        <Tab href={`/repos/${id}/graph`} label="Graph" />
        <Tab href={`/repos/${id}/decisions`} label="Decisions" />
      </nav>

      <div className="grid gap-6 md:grid-cols-3 mb-8">
        <MetricCard label="Files" value={overview?.total_files ?? 0} />
        <MetricCard label="Functions" value={overview?.total_functions ?? 0} />
        <MetricCard label="Classes" value={overview?.total_classes ?? 0} />
      </div>

      {health && (
        <section className="mb-8">
          <h2 className="text-lg font-semibold mb-4">Health Score</h2>
          <div className="grid gap-4 md:grid-cols-4">
            <ScoreCard label="Overall" value={health.overall} />
            <ScoreCard label="Defect" value={health.defect} />
            <ScoreCard label="Maintainability" value={health.maintainability} />
            <ScoreCard label="Performance" value={health.performance} />
          </div>
          {health.kpis && Object.keys(health.kpis).length > 0 && (
            <div className="mt-6">
              <h3 className="text-sm font-medium mb-3">KPIs</h3>
              <div className="grid gap-3 md:grid-cols-3">
                {Object.entries(health.kpis).map(([k, v]) => (
                  <div key={k} className="rounded-lg border border-[var(--border)] p-3">
                    <div className="text-xs text-gray-500 uppercase tracking-wide">{k}</div>
                    <div className="text-lg font-semibold mt-1">{typeof v === "number" ? v.toFixed(2) : v}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>
      )}

      {cost && (
        <section>
          <h2 className="text-lg font-semibold mb-4">LLM Cost Estimate</h2>
          <MetricCard label="Estimated Cost" value={`$${cost.estimated_cost_usd.toFixed(4)}`} />
        </section>
      )}
    </div>
  );
}

function Tab({ href, label, active }: { href: string; label: string; active?: boolean }) {
  return (
    <Link
      href={href}
      className={`text-sm pb-2 border-b-2 transition-colors ${
        active
          ? "border-indigo-500 text-indigo-600 dark:text-indigo-400"
          : "border-transparent text-gray-500 hover:text-[var(--fg)]"
      }`}
    >
      {label}
    </Link>
  );
}

function MetricCard({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-xl border border-[var(--border)] p-4">
      <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">{label}</div>
      <div className="text-2xl font-bold">{value}</div>
    </div>
  );
}

function ScoreCard({ label, value }: { label: string; value: number }) {
  const color = value >= 80 ? "text-green-500" : value >= 50 ? "text-yellow-500" : "text-red-500";
  return (
    <div className="rounded-xl border border-[var(--border)] p-4 text-center">
      <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">{label}</div>
      <div className={`text-3xl font-bold ${color}`}>{value.toFixed(1)}</div>
    </div>
  );
}
