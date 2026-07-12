from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from core.pipeline.checkpoint import PipelineCheckpoint, compute_fingerprint
from core.pipeline.modes import OrchestratorMode
from core.pipeline.phases.analysis import run_analysis
from core.pipeline.phases.generation import run_generation
from core.pipeline.phases.ingestion import run_ingestion
from core.pipeline.progress import ProgressCallback


@dataclass
class PipelineResult:
    deps: dict[str, list[str]] = field(default_factory=dict)
    entry_funcs: list[str] = field(default_factory=list)
    linenos: dict[str, int] = field(default_factory=dict)
    complexities: dict[str, int] = field(default_factory=dict)
    graph: Any = None
    dead_code: list[str] = field(default_factory=list)
    cycles: list[list[str]] = field(default_factory=list)
    entry_points: list[str] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    generated: dict[str, Any] = field(default_factory=dict)
    file_count: int = 0
    symbol_count: int = 0
    languages: set[str] = field(default_factory=set)
    elapsed_seconds: float = 0.0


async def run_pipeline(
    repo_path: Path | str,
    *,
    mode: OrchestratorMode = OrchestratorMode.STANDARD,
    use_cache: bool = True,
    respect_gitignore: bool = True,
    generate_docs: bool = False,
    llm_client: Any = None,
    changed_funcs: list[str] | None = None,
    limit: int = 10,
    resume: bool = False,
    progress: ProgressCallback | None = None,
) -> PipelineResult:
    repo_path = Path(repo_path).resolve()
    start = time.monotonic()

    checkpointer: Optional[PipelineCheckpoint] = None
    if resume:
        checkpointer = PipelineCheckpoint.load(repo_path)
        if checkpointer is None:
            checkpointer = PipelineCheckpoint(
                started_at=start,
                fingerprint=compute_fingerprint(repo_path),
            )
        if checkpointer.can_skip("ingestion"):
            if progress:
                progress.on_message("info", "  ↳ Resuming — skip ingestion")
            ingestion_result = None
        else:
            ingestion_result = await run_ingestion(
                repo_path,
                respect_gitignore=respect_gitignore,
                use_cache=use_cache,
                progress=progress,
            )
            checkpointer.completed_phases.add("ingestion")
            checkpointer.running_phase = None
    else:
        ingestion_result = await run_ingestion(
            repo_path,
            respect_gitignore=respect_gitignore,
            use_cache=use_cache,
            progress=progress,
        )

    deps = ingestion_result["deps"]
    entry_funcs = ingestion_result["entry_funcs"]
    linenos = ingestion_result["linenos"]
    complexities = ingestion_result["complexities"]
    graph = ingestion_result["graph"]
    file_count = len(deps)

    if resume and checkpointer and checkpointer.can_skip("analysis"):
        if progress:
            progress.on_message("info", "  ↳ Resuming — skip analysis")
        analysis_result = None
    else:
        analysis_result = await run_analysis(
            repo_path,
            graph=graph,
            deps=deps,
            entry_funcs=entry_funcs,
            linenos=linenos,
            complexities=complexities,
            changed_funcs=changed_funcs,
            limit=limit,
            progress=progress,
        )
        if checkpointer:
            checkpointer.completed_phases.add("analysis")
            checkpointer.running_phase = None

    dead_code = analysis_result["dead_code"] if analysis_result else []
    cycles = analysis_result["cycles"] if analysis_result else []
    entry_points = analysis_result["entry_points"] if analysis_result else []
    summary = analysis_result["summary"] if analysis_result else {}

    if generate_docs:
        generated = await run_generation(
            repo_path,
            graph=graph,
            deps=deps,
            entry_funcs=entry_funcs,
            summary=summary,
            generate_docs=generate_docs,
            progress=progress,
            llm_client=llm_client,
        )
    else:
        generated = {}

    if checkpointer:
        checkpointer.completed_phases.add("generation")
        checkpointer.save(repo_path)

    elapsed = time.monotonic() - start

    return PipelineResult(
        deps=deps,
        entry_funcs=entry_funcs,
        linenos=linenos,
        complexities=complexities,
        graph=graph,
        dead_code=dead_code,
        cycles=cycles,
        entry_points=entry_points,
        summary=summary,
        generated=generated,
        file_count=file_count,
        elapsed_seconds=elapsed,
    )
