from __future__ import annotations

from typing import Any

from core.utils import ensure_parent, write_json


def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    """Write a Phase 1 (baseline) markdown report.

    The report cites artifact paths so readers can verify the numbers
    independently of the prose.

    Parameters
    ----------
    report_path : Path-like
        Where to write the ``phase1_report.md`` file.
    source_summary : dict
        Raw/clean record counts and source metadata.
    metrics : dict
        ``baseline_metrics.json`` content.
    quality : dict
        Output of ``run_data_quality_checks``.
    freshness : dict
        Output of ``build_freshness_report``.
    """
    ensure_parent(report_path)

    lines: list[str] = []
    add = lines.append

    add("# Phase 1 — Baseline Pipeline Report")
    add("")
    add("> This report was generated automatically by the pipeline.  "
        "All numbers trace back to artifacts on disk; do not edit manually.")
    add("")

    # ── Source & ingestion ──────────────────────────────────────────────
    add("## 1. Source & Ingestion")
    add("")
    add(f"| Field | Value |")
    add(f"| --- | --- |")
    add(f"| API | {source_summary.get('source_api','N/A')} |")
    add(f"| Query | {source_summary.get('source_query','N/A')} |")
    add(f"| Filter | {source_summary.get('source_filter','N/A')} |")
    add(f"| max_results | {source_summary.get('max_results','N/A')} |")
    add(f"| Raw items fetched | {source_summary.get('raw_items','N/A')} |")
    add(f"| Raw records parsed | {source_summary.get('raw_records','N/A')} |")
    add(f"| raw_api_response | `{source_summary.get('raw_response_path','N/A')}` |")
    add(f"| raw_records_json | `{source_summary.get('raw_records_path','N/A')}` |")
    add("")

    # ── Cleaning ────────────────────────────────────────────────────────
    audit = {}
    if source_summary.get("raw_items") and source_summary.get("raw_records"):
        r_in = source_summary.get("raw_items", 0)
        r_out = source_summary.get("raw_records", 0)
        if r_in and r_out:
            add("## 2. Cleaning")
            add("")
            add(f"| Field | Value |")
            add(f"| --- | --- |")
            add(f"| Input records | {r_in} |")
            add(f"| Output records | {r_out} |")
            drop = r_in - r_out
            if drop > 0:
                add(f"| Records dropped | {drop} |")
            else:
                add(f"| Records dropped | 0 |")
            add(f"| clean_csv | `data/clean/papers_clean.csv` |")
            add(f"| clean_json | `data/clean/papers_clean.json` |")
            add("")

    # ── Data quality ────────────────────────────────────────────────────
    add("## 3. Data Quality Checks")
    add("")
    q_checks = quality.get("checks", [])
    if q_checks:
        add(f"| Check | Passed | Detail |")
        add(f"| --- | --- | --- |")
        for c in q_checks:
            icon = "✅" if c["passed"] else "❌"
            detail = c.get("detail", "")
            count = c.get("count")
            count_str = f" (count={count})" if count is not None else ""
            add(f"| {icon} {c['name']} | {c['passed']} | {detail}{count_str} |")
        add("")
        add(f"**Overall: {'✅ PASS' if quality.get('overall_passed') else '❌ FAIL'}** — {quality.get('summary','')}")
        add("")
    else:
        add("*No quality checks were run.*")
        add("")

    # ── Freshness ──────────────────────────────────────────────────────
    add("## 4. Freshness")
    add("")
    add(f"| Field | Value |")
    add(f"| --- | --- |")
    add(f"| Latest published | {freshness.get('latest_published','N/A')} |")
    add(f"| Oldest published | {freshness.get('oldest_published','N/A')} |")
    add(f"| Total rows | {freshness.get('total_rows','N/A')} |")
    add(f"| Stale rows (> {freshness.get('threshold_days','?')} days) | {freshness.get('stale_rows','N/A')} |")
    add(f"| Is fresh | {freshness.get('is_fresh','N/A')} |")
    add(f"| freshness_report | `data/quality/freshness_report.json` |")
    add("")
    if freshness.get("is_fresh"):
        add("> **All papers are within the freshness threshold.**")
    else:
        add(f"> ⚠️ **{freshness.get('stale_rows')} papers exceed the freshness threshold of {freshness.get('threshold_days')} days.**")
    add("")

    # ── Evaluation metrics ──────────────────────────────────────────────
    add("## 5. Evaluation Metrics")
    add("")
    m = metrics
    if m:
        add(f"| Metric | Value |")
        add(f"| --- | --- |")
        add(f"| Samples | {m.get('samples','N/A')} |")
        add(f"| retrieval_hit_rate | {m.get('retrieval_hit_rate','N/A'):.3f} |" if isinstance(m.get("retrieval_hit_rate"), float) else f"| retrieval_hit_rate | {m.get('retrieval_hit_rate','N/A')} |")
        add(f"| mean_token_f1 | {m.get('mean_token_f1','N/A'):.3f} |" if isinstance(m.get("mean_token_f1"), float) else f"| mean_token_f1 | {m.get('mean_token_f1','N/A')} |")
        add(f"| judge_accuracy | {m.get('judge_accuracy','N/A'):.3f} |" if isinstance(m.get("judge_accuracy"), float) else f"| judge_accuracy | {m.get('judge_accuracy','N/A')} |")
        add(f"| mean_judge_score | {m.get('mean_judge_score','N/A'):.3f} |" if isinstance(m.get("mean_judge_score"), float) else f"| mean_judge_score | {m.get('mean_judge_score','N/A')} |")
        add(f"| baseline_metrics | `data/results/baseline_metrics.json` |")
        add(f"| baseline_answers | `data/results/baseline_answers.json` |")
        add("")
    else:
        add("*No evaluation metrics available (pipeline not run or failed).*")
        add("")

    # ── Artifacts ───────────────────────────────────────────────────────
    add("## 6. Artifact Checklist")
    add("")
    add("| Artifact | Status | Path |")
    add("| --- | --- | --- |")
    for name, path in [
        ("Raw API response", source_summary.get("raw_response_path", "")),
        ("Raw records JSON", source_summary.get("raw_records_path", "")),
        ("Clean CSV", "data/clean/papers_clean.csv"),
        ("Clean JSON", "data/clean/papers_clean.json"),
        ("Test set", "data/eval/test_set.json"),
        ("Baseline metrics", "data/results/baseline_metrics.json"),
        ("Baseline answers", "data/results/baseline_answers.json"),
        ("Quality report", "data/quality/quality_baseline.json"),
        ("Freshness report", "data/quality/freshness_report.json"),
        ("Phase 1 report", "data/reports/phase1_report.md"),
    ]:
        status = "✅ present" if path else "⚠️ missing"
        display = path.split("/")[-1] if "/" in path else path
        add(f"| {name} | {status} | `{display}` |")
    add("")

    text = "\n".join(lines)
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write(text)


def generate_corruption_report(
    report_path,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
    baseline_quality: dict[str, Any] | None = None,
    baseline_freshness: dict[str, Any] | None = None,
) -> None:
    """Write a corruption vs baseline vs repaired comparison markdown report.

    Shows side-by-side metrics and quality/freshness deltas so the lab team
    can demonstrate that (a) corruption measurably degrades the agent and
    (b) repair from raw restores quality.
    """
    ensure_parent(report_path)

    lines: list[str] = []
    add = lines.append

    add("# Corruption Impact & Repair Comparison Report")
    add("")
    add("> Generated automatically.  All values trace to `data/results/` artifacts.")
    add("")

    def metric_row(label: str, baseline: Any, corrupted: Any, repaired: Any) -> None:
        def fmt(v):
            if isinstance(v, float):
                return f"{v:.3f}"
            return str(v) if v is not None else "—"

        baseline_str = fmt(baseline)
        corrupted_str = fmt(corrupted)
        repaired_str = fmt(repaired)
        # Highlight deltas
        arrow = ""
        if baseline is not None and corrupted is not None:
            try:
                delta = float(corrupted) - float(baseline)
                arrow = f" ({delta:+.3f})"
            except (TypeError, ValueError):
                pass
        add(f"| {label} | {baseline_str} | {corrupted_str}{arrow} | {repaired_str} |")

    add("## 1. Evaluation Metrics Comparison")
    add("")
    add("| Metric | Baseline | Corrupted (Δ) | Repaired |")
    add("| --- | --- | --- | --- |")
    metric_row(
        "retrieval_hit_rate",
        baseline_metrics.get("retrieval_hit_rate"),
        corrupted_metrics.get("retrieval_hit_rate"),
        repaired_metrics.get("retrieval_hit_rate"),
    )
    metric_row(
        "mean_token_f1",
        baseline_metrics.get("mean_token_f1"),
        corrupted_metrics.get("mean_token_f1"),
        repaired_metrics.get("mean_token_f1"),
    )
    metric_row(
        "judge_accuracy",
        baseline_metrics.get("judge_accuracy"),
        corrupted_metrics.get("judge_accuracy"),
        repaired_metrics.get("judge_accuracy"),
    )
    metric_row(
        "mean_judge_score",
        baseline_metrics.get("mean_judge_score"),
        corrupted_metrics.get("mean_judge_score"),
        repaired_metrics.get("mean_judge_score"),
    )
    metric_row(
        "samples",
        baseline_metrics.get("samples"),
        corrupted_metrics.get("samples"),
        repaired_metrics.get("samples"),
    )
    add("")

    def quality_summary(label: str, quality: dict[str, Any]) -> None:
        checks = quality.get("checks", [])
        if checks:
            total = len(checks)
            ok = sum(1 for c in checks if c["passed"])
            value = f"{ok}/{total} checks passed"
        else:
            passed = quality.get("overall_passed", quality.get("passed"))
            value = "PASS" if passed is True else "FAIL" if passed is False else "unavailable"
        add(f"| {label} quality | {value} |")

    add("## 2. Data Quality")
    add("")
    add("| Dataset | Quality gates |")
    add("| --- | --- |")
    quality_summary("Baseline", baseline_quality or {})
    quality_summary("Corrupted", corrupted_quality)
    quality_summary("Repaired", repaired_quality)
    add("")

    add("## 3. Freshness")
    add("")
    add("| Dataset | Total rows | Stale rows | Is fresh |")
    add("| --- | --- | --- | --- |")
    baseline_freshness = baseline_freshness or {}
    add(f"| Baseline | {baseline_freshness.get('total_rows','?')} | {baseline_freshness.get('stale_rows','?')} | {baseline_freshness.get('is_fresh','?')} |")
    add(f"| Corrupted | {corrupted_freshness.get('total_rows','?')} | {corrupted_freshness.get('stale_rows','?')} | {corrupted_freshness.get('is_fresh','?')} |")
    add(f"| Repaired | {repaired_freshness.get('total_rows','?')} | {repaired_freshness.get('stale_rows','?')} | {repaired_freshness.get('is_fresh','?')} |")
    add("")

    # ── Findings ────────────────────────────────────────────────────────
    add("## 4. Key Findings")
    add("")
    add("*To be filled in by the team after reviewing the comparison data above.*")
    add("")
    add("- **Corruption impact:** _describe how metrics changed and which check caught the corruption_")
    add("- **Repair fidelity:** _describe whether metrics recovered and which rows were restored_")
    add("- **Limitations:** _any metric that did not recover, or recovered incompletely_")
    add("")

    text = "\n".join(lines)
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write(text)
