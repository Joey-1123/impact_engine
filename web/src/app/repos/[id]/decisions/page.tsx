import Link from "next/link";
import { getDecisions } from "@/lib/api";

export default async function DecisionsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  let data: Awaited<ReturnType<typeof getDecisions>> = { decisions: [], total: 0 };
  try {
    data = await getDecisions(id);
  } catch {}

  return (
    <div className="min-h-screen p-8">
      <header className="mb-8">
        <Link href="/" className="text-sm text-indigo-500 hover:underline mb-2 inline-block">&larr; Dashboard</Link>
        <h1 className="text-2xl font-bold">Decisions — {id}</h1>
      </header>

      <nav className="flex gap-4 mb-8 border-b border-[var(--border)] pb-2">
        <Tab href={`/repos/${id}`} label="Overview" />
        <Tab href={`/repos/${id}/graph`} label="Graph" />
        <Tab href={`/repos/${id}/decisions`} label="Decisions" active />
      </nav>

      <div className="mb-6">
        <Metric label="Total Decisions" value={data.total} />
      </div>

      <div className="space-y-4">
        {data.decisions.map((d: { title: string; decision: string; rationale: string; source: string; confidence: number; status: string }, i: number) => (
          <div key={i} className="rounded-xl border border-[var(--border)] p-5">
            <div className="flex items-start justify-between gap-4 mb-2">
              <h3 className="font-semibold">{d.title}</h3>
              <span className={`shrink-0 px-2 py-0.5 rounded text-xs font-medium ${
                d.status === "active" ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200" :
                d.status === "deprecated" ? "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200" :
                "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200"
              }`}>{d.status}</span>
            </div>
            <p className="text-sm text-gray-500 mb-2">{d.decision}</p>
            {d.rationale && <p className="text-xs text-gray-400 mb-2">{d.rationale.slice(0, 300)}</p>}
            <div className="flex items-center gap-3 text-xs text-gray-400">
              <span>Source: {d.source}</span>
              <span>Confidence: {(d.confidence * 100).toFixed(0)}%</span>
            </div>
          </div>
        ))}
        {data.decisions.length === 0 && (
          <div className="text-center py-12 text-gray-500">No decisions found</div>
        )}
      </div>
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

function Metric({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-xl border border-[var(--border)] p-4 inline-block">
      <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">{label}</div>
      <div className="text-2xl font-bold">{value}</div>
    </div>
  );
}
