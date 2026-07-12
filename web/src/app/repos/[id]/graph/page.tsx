import Link from "next/link";
import { getGraph } from "@/lib/api";

export default async function GraphPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  let graph: Awaited<ReturnType<typeof getGraph>> = { nodes: [], edges: [], layers: [], fingerprint: "" };
  try {
    graph = await getGraph(id);
  } catch {}

  const nodesByLayer: Record<string, number> = {};
  for (const n of graph.nodes) {
    nodesByLayer[n.layer] = (nodesByLayer[n.layer] || 0) + 1;
  }

  return (
    <div className="min-h-screen p-8">
      <header className="mb-8">
        <Link href="/" className="text-sm text-indigo-500 hover:underline mb-2 inline-block">&larr; Dashboard</Link>
        <h1 className="text-2xl font-bold">Knowledge Graph — {id}</h1>
      </header>

      <nav className="flex gap-4 mb-8 border-b border-[var(--border)] pb-2">
        <Tab href={`/repos/${id}`} label="Overview" />
        <Tab href={`/repos/${id}/graph`} label="Graph" active />
        <Tab href={`/repos/${id}/decisions`} label="Decisions" />
      </nav>

      <div className="grid gap-6 md:grid-cols-3 mb-8">
        <Metric label="Nodes" value={graph.nodes.length} />
        <Metric label="Edges" value={graph.edges.length} />
        <Metric label="Fingerprint" value={graph.fingerprint.slice(0, 12)} />
      </div>

      {graph.layers.length > 0 && (
        <section className="mb-8">
          <h2 className="text-lg font-semibold mb-4">Layers</h2>
          <div className="flex flex-wrap gap-2">
            {graph.layers.map((layer) => (
              <span key={layer} className="px-3 py-1 rounded-full text-sm bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200">
                {layer} ({nodesByLayer[layer] ?? 0})
              </span>
            ))}
          </div>
        </section>
      )}

      <section>
        <h2 className="text-lg font-semibold mb-4">Top Nodes by PageRank</h2>
        <div className="overflow-x-auto rounded-xl border border-[var(--border)]">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-[var(--muted)] border-b border-[var(--border)]">
                <th className="text-left p-3 font-medium">Label</th>
                <th className="text-left p-3 font-medium">Layer</th>
                <th className="text-left p-3 font-medium">Type</th>
                <th className="text-right p-3 font-medium">PageRank</th>
                <th className="text-left p-3 font-medium">Complexity</th>
              </tr>
            </thead>
            <tbody>
              {graph.nodes.slice(0, 30).map((n: { id: string; label: string; file_path: string; layer: string; type: string; pagerank: number; complexity: string }) => (
                <tr key={n.id} className="border-b border-[var(--border)] last:border-0 hover:bg-[var(--muted)]">
                  <td className="p-3 font-mono text-xs max-w-[300px] truncate" title={n.file_path}>{n.label}</td>
                  <td className="p-3">{n.layer}</td>
                  <td className="p-3">
                    <span className={`px-2 py-0.5 rounded text-xs ${n.type === "function" ? "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200" : "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"}`}>
                      {n.type}
                    </span>
                  </td>
                  <td className="p-3 text-right font-mono">{n.pagerank.toFixed(6)}</td>
                  <td className="p-3">
                    <ComplexityBadge level={n.complexity} />
                  </td>
                </tr>
              ))}
              {graph.nodes.length === 0 && (
                <tr><td colSpan={5} className="p-6 text-center text-gray-500">No graph data available</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
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
    <div className="rounded-xl border border-[var(--border)] p-4">
      <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">{label}</div>
      <div className="text-2xl font-bold">{value}</div>
    </div>
  );
}

function ComplexityBadge({ level }: { level: string }) {
  const colors: Record<string, string> = {
    simple: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
    moderate: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
    complex: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
  };
  return (
    <span className={`px-2 py-0.5 rounded text-xs ${colors[level] || "bg-gray-100 text-gray-800"}`}>
      {level}
    </span>
  );
}
