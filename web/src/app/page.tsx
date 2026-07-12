import Link from "next/link";
import { Activity, BarChart3, FileText, GitBranch, Layers, Search } from "lucide-react";
import { getHealth } from "@/lib/api";

export default async function HomePage() {
  let health = { status: "unknown", version: "" };
  try {
    health = await getHealth();
  } catch {}

  return (
    <div className="min-h-screen p-8">
      <header className="mb-12">
        <div className="flex items-center gap-3 mb-2">
          <Activity className="w-8 h-8 text-indigo-500" />
          <h1 className="text-3xl font-bold">Impact Engine</h1>
        </div>
        <p className="text-gray-500 dark:text-gray-400">
          Codebase intelligence platform
          {health.status && (
            <span className="ml-4 inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
              <span className="w-1.5 h-1.5 rounded-full bg-green-500" />
              {health.status} v{health.version}
            </span>
          )}
        </p>
      </header>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <FeatureCard
          href="/repos/default"
          icon={BarChart3}
          title="Code Health"
          description="3D scoring: defect, maintainability, and performance metrics with calibrated biomarkers"
        />
        <FeatureCard
          href="/repos/default/graph"
          icon={Layers}
          title="Knowledge Graph"
          description="PageRank centrality, community detection, layer inference, and guided codebase tour"
        />
        <FeatureCard
          href="/repos/default/decisions"
          icon={FileText}
          title="Decision Mining"
          description="Extract architectural decisions from changelogs, PRs, and ADR files"
        />
        <FeatureCard
          icon={Search}
          title="Vector Search"
          description="Semantic search over code with cosine similarity and embedder-agnostic vector store"
        />
        <FeatureCard
          icon={GitBranch}
          title="Blame & Contributors"
          description="Per-line blame index, bus factor, contributor profiles, and ownership analysis"
        />
        <FeatureCard
          icon={Activity}
          title="Refactoring Analysis"
          description="Cycle-breaking via MFAS, file-splitting suggestions, PR blast radius scoring"
        />
      </div>
    </div>
  );
}

function FeatureCard({
  href,
  icon: Icon,
  title,
  description,
}: {
  href?: string;
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  description: string;
}) {
  const content = (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--bg)] p-6 hover:shadow-md transition-shadow h-full">
      <div className="flex items-center gap-3 mb-3">
        <div className="p-2 rounded-lg bg-indigo-100 dark:bg-indigo-900/50">
          <Icon className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
        </div>
        <h2 className="text-lg font-semibold">{title}</h2>
      </div>
      <p className="text-sm text-gray-500 dark:text-gray-400">{description}</p>
    </div>
  );

  if (href) return <Link href={href}>{content}</Link>;
  return content;
}
