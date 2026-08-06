from __future__ import annotations

from pathlib import Path
from typing import Any

import altair as alt
import pandas as pd
import streamlit as st

from core.config import Settings, normalized_provider, require_llm_credentials
from core.utils import read_json
from retrieval.agent import build_agent, run_agent_question
from retrieval.index import LocalEmbeddingIndex
from retrieval.qa import answer_question

STATES = ["baseline", "corrupted", "repaired"]
STATE_LABELS = {"baseline": "Baseline", "corrupted": "Corrupted", "repaired": "Repaired"}
STATE_COLORS = {"baseline": "#2a78d6", "corrupted": "#eb6834", "repaired": "#1baf7a"}
METRIC_LABELS = {
    "retrieval_hit_rate": "Retrieval hit rate",
    "mean_token_f1": "Mean token F1",
    "judge_accuracy": "Judge accuracy",
    "mean_judge_score": "Mean judge score (1-5)",
}


# ---------------------------------------------------------------------------
# Cached resources / data
# ---------------------------------------------------------------------------


@st.cache_resource
def get_settings() -> Settings:
    from core.config import load_settings

    return load_settings()


@st.cache_resource
def load_index_cached(embeddings_path: str) -> LocalEmbeddingIndex:
    return LocalEmbeddingIndex.load(get_settings(), Path(embeddings_path))


@st.cache_resource
def build_agent_cached(embeddings_path: str):
    return build_agent(get_settings(), load_index_cached(embeddings_path))


@st.cache_data
def read_json_cached(path: str, _mtime: float) -> Any:
    return read_json(Path(path))


def read_json_if_exists(path: Path) -> Any | None:
    if not path.exists():
        return None
    return read_json_cached(str(path), path.stat().st_mtime)


# ---------------------------------------------------------------------------
# Per-state artifact path helpers
# ---------------------------------------------------------------------------


def embeddings_path(settings: Settings, state: str) -> Path:
    return {
        "baseline": settings.paths.embeddings_json,
        "corrupted": settings.paths.corrupted_embeddings_json,
        "repaired": settings.paths.repaired_embeddings_json,
    }[state]


def clean_csv_path(settings: Settings, state: str) -> Path:
    return {
        "baseline": settings.paths.clean_csv,
        "corrupted": settings.paths.corrupted_clean_csv,
        "repaired": settings.paths.repaired_clean_csv,
    }[state]


def metrics_path(settings: Settings, state: str) -> Path:
    return {
        "baseline": settings.paths.baseline_metrics,
        "corrupted": settings.paths.corrupted_metrics,
        "repaired": settings.paths.repaired_metrics,
    }[state]


def answers_path(settings: Settings, state: str) -> Path:
    return {
        "baseline": settings.paths.baseline_answers,
        "corrupted": settings.paths.corrupted_answers,
        "repaired": settings.paths.repaired_answers,
    }[state]


def quality_path(settings: Settings, state: str) -> Path:
    if state == "baseline":
        return settings.paths.quality_dir / "quality_baseline.json"
    return settings.paths.quality_dir / f"{state}_quality.json"


def freshness_path(settings: Settings, state: str) -> Path:
    if state == "baseline":
        return settings.paths.freshness_report
    return settings.paths.quality_dir / f"freshness_{state}.json"


def cleaning_audit_path(settings: Settings, state: str) -> Path | None:
    if state == "corrupted":
        return None
    return settings.paths.quality_dir / f"cleaning_audit_{state}.json"


def exists(path: Path | None) -> bool:
    return path is not None and path.exists()


def available_states(settings: Settings) -> list[str]:
    return [s for s in STATES if exists(embeddings_path(settings, s))]


# ---------------------------------------------------------------------------
# Page: Overview
# ---------------------------------------------------------------------------


def render_overview(settings: Settings) -> None:
    st.title("Pipeline Overview")

    cols = st.columns(3)
    for col, state in zip(cols, STATES, strict=False):
        ready = exists(embeddings_path(settings, state)) and exists(metrics_path(settings, state))
        col.metric(STATE_LABELS[state], "Ready" if ready else "Not built yet")

    st.subheader("Artifacts")
    rows = []

    def row(artifact: str, state: str, path: Path | None) -> None:
        count = None
        if exists(path):
            if path.suffix == ".json":
                payload = read_json_if_exists(path)
                if isinstance(payload, list):
                    count = len(payload)
                elif isinstance(payload, dict) and "documents" in payload:
                    count = len(payload["documents"])
            elif path.suffix == ".csv":
                count = sum(1 for _ in path.open(encoding="utf-8")) - 1
        rows.append(
            {
                "Artifact": artifact,
                "State": STATE_LABELS[state],
                "Exists": "✅" if exists(path) else "⏳",
                "Rows/Docs": str(count) if count is not None else "-",
                "Path": str(path) if path else "-",
            }
        )

    row("Raw response", "baseline", settings.paths.raw_api_response)
    row("Raw records", "baseline", settings.paths.raw_records_json)
    for state in STATES:
        row("Clean data", state, clean_csv_path(settings, state))
    for state in STATES:
        row("Embedding manifest", state, embeddings_path(settings, state))
    row("Eval test set", "baseline", settings.paths.eval_testset)
    for state in STATES:
        row("Metrics", state, metrics_path(settings, state))
    for state in STATES:
        row("Answers", state, answers_path(settings, state))
    for state in STATES:
        row("Quality report", state, quality_path(settings, state))
    for state in STATES:
        row("Freshness report", state, freshness_path(settings, state))
    row("Corruption log", "corrupted", settings.paths.corruption_log)
    row("Phase 1 report", "baseline", settings.paths.baseline_report)
    row("Comparison report", "corrupted", settings.paths.comparison_report)

    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)


# ---------------------------------------------------------------------------
# Page: RAG Explorer
# ---------------------------------------------------------------------------


def render_rag_explorer(settings: Settings) -> None:
    st.title("RAG Explorer")

    states = available_states(settings)
    if not states:
        st.warning("Chưa có embedding manifest nào (baseline/corrupted/repaired). Chờ pipeline chạy xong.")
        return

    state = st.selectbox("Collection", states, format_func=lambda s: STATE_LABELS[s])
    path = embeddings_path(settings, state)
    index = load_index_cached(str(path))
    st.caption(f"Collection: `{index.collection_name}` — {index.collection.count()} documents")

    tab_search, tab_lookup, tab_chat = st.tabs(["Semantic Search", "Exact Lookup", "Agent Chat"])

    with tab_search:
        query = st.text_input("Query", value="oil and gas safety report generation", key=f"query_{state}")
        top_k = st.slider("top_k", 1, 10, 4, key=f"topk_{state}")
        if query:
            results = index.search(query, top_k=top_k)
            if not results:
                st.info("Không có kết quả.")
            for r in results:
                with st.expander(f"score={r.score:.3f} — {r.title}"):
                    st.write(f"**paper_id**: {r.paper_id}")
                    st.write(r.content)
                    st.json(r.metadata)

    with tab_lookup:
        needle = st.text_input("paper_id hoặc title (chính xác)", key=f"lookup_{state}")
        if needle:
            hit = index.lookup(needle)
            if hit:
                st.success("Found")
                st.json(hit)
            else:
                st.info("Không tìm thấy record khớp chính xác.")

    with tab_chat:
        history_key = f"chat_{state}"
        if history_key not in st.session_state:
            st.session_state[history_key] = []

        if st.button("Clear chat", key=f"clear_{state}"):
            st.session_state[history_key] = []

        credentials_ok = True
        credentials_error = ""
        try:
            require_llm_credentials(settings)
        except RuntimeError as exc:
            credentials_ok = False
            credentials_error = str(exc)

        if not credentials_ok:
            st.warning(
                f"Chưa cấu hình LLM credentials ({credentials_error}) — dùng answer_question (no-LLM) thay thế."
            )
        else:
            st.caption(f"LLM provider: {normalized_provider(settings)} / {settings.model_name}")

        for role, content in st.session_state[history_key]:
            with st.chat_message(role):
                st.write(content)

        question = st.chat_input("Hỏi về corpus...", key=f"chat_input_{state}")
        if question:
            st.session_state[history_key].append(("user", question))
            with st.chat_message("user"):
                st.write(question)
            with st.chat_message("assistant"):
                if credentials_ok:
                    agent = build_agent_cached(str(path))
                    answer = run_agent_question(agent, question)
                else:
                    result = answer_question(question, settings, index)
                    answer = result.answer
                st.write(answer)
            st.session_state[history_key].append(("assistant", answer))


# ---------------------------------------------------------------------------
# Page: Evaluation
# ---------------------------------------------------------------------------


def render_evaluation(settings: Settings) -> None:
    st.title("Evaluation")

    summaries: dict[str, dict[str, Any]] = {}
    for state in STATES:
        payload = read_json_if_exists(metrics_path(settings, state))
        if payload is not None:
            summaries[state] = payload

    if not summaries:
        st.warning("Chưa có metrics nào được sinh ra.")
        return

    metric_keys = list(METRIC_LABELS.keys())
    table = pd.DataFrame(
        {STATE_LABELS[state]: [summaries[state].get(key) for key in metric_keys] for state in summaries},
        index=[METRIC_LABELS[key] for key in metric_keys],
    )
    st.dataframe(table, width="stretch")

    chart_rows = [
        {"Metric": METRIC_LABELS[key], "State": STATE_LABELS[state], "Value": summaries[state].get(key)}
        for state in summaries
        for key in metric_keys
    ]
    chart_df = pd.DataFrame(chart_rows)
    color_scale = alt.Scale(
        domain=[STATE_LABELS[s] for s in STATES if s in summaries],
        range=[STATE_COLORS[s] for s in STATES if s in summaries],
    )
    chart = (
        alt.Chart(chart_df)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("State:N", title=None, axis=alt.Axis(labels=False, ticks=False)),
            y=alt.Y("Value:Q", title="Giá trị"),
            color=alt.Color("State:N", scale=color_scale, legend=alt.Legend(title="Trạng thái")),
            column=alt.Column("Metric:N", title=None),
            tooltip=["Metric", "State", "Value"],
        )
        .properties(width=140)
    )
    st.altair_chart(chart, width="content")

    st.subheader("Answers")
    state = st.selectbox("State", list(summaries.keys()), format_func=lambda s: STATE_LABELS[s], key="answers_state")
    answers = read_json_if_exists(answers_path(settings, state))
    if not answers:
        st.info("Chưa có answers cho state này.")
        return

    question_map = {f"{a['question_type']} — {a['question'][:60]}": a for a in answers}
    selected_label = st.selectbox("Câu hỏi", list(question_map.keys()), key="answer_pick")
    selected = question_map[selected_label]
    st.write(f"**Question**: {selected['question']}")
    st.write(f"**Ground truth**: {selected['ground_truth']}")
    st.write(f"**Answer**: {selected['answer']}")
    col1, col2, col3 = st.columns(3)
    col1.metric("Retrieval hit", "✅" if selected["retrieval_hit"] else "❌")
    col2.metric("Token F1", f"{selected['token_f1']:.2f}")
    col3.metric("Judge score", f"{selected['judge']['score']}/5")
    with st.expander("Judge reasoning & retrieved contexts"):
        st.write(selected["judge"]["reasoning"])
        for ctx in selected["retrieved_contexts"]:
            st.text(ctx)


# ---------------------------------------------------------------------------
# Page: Data Quality & Freshness
# ---------------------------------------------------------------------------


def render_quality(settings: Settings) -> None:
    st.title("Data Quality & Freshness")

    cols = st.columns(3)
    for col, state in zip(cols, STATES, strict=False):
        with col:
            st.subheader(STATE_LABELS[state])
            quality = read_json_if_exists(quality_path(settings, state))
            if quality is None:
                st.info("Chưa có quality report.")
            else:
                st.metric("Overall", "PASS" if quality.get("overall_passed") else "FAIL")
                checks_df = pd.DataFrame(
                    [
                        {"Check": c["name"], "Passed": "✅" if c["passed"] else "❌", "Detail": c["detail"]}
                        for c in quality.get("checks", [])
                    ]
                )
                st.dataframe(checks_df, width="stretch", hide_index=True)

            freshness = read_json_if_exists(freshness_path(settings, state))
            if freshness is None:
                st.info("Chưa có freshness report.")
            else:
                st.metric(
                    "Freshness",
                    "Fresh" if freshness.get("is_fresh") else "Stale",
                    delta=f"{freshness.get('stale_rows')}/{freshness.get('total_rows')} stale",
                    delta_color="inverse",
                )
                st.caption(
                    f"Latest: {freshness.get('latest_published')} · Oldest: {freshness.get('oldest_published')}"
                )

            audit_path = cleaning_audit_path(settings, state)
            audit = read_json_if_exists(audit_path) if audit_path else None
            if audit:
                st.caption(
                    f"Cleaning audit: {audit['input_rows']} → {audit['output_rows']} rows "
                    f"({audit['duplicate_rows_removed']} dup removed, {audit['filtered_rows']} filtered)"
                )


# ---------------------------------------------------------------------------
# Page: Corruption & Reports
# ---------------------------------------------------------------------------


def render_corruption_reports(settings: Settings) -> None:
    st.title("Corruption Log & Reports")

    log = read_json_if_exists(settings.paths.corruption_log)
    if log is None:
        st.info("Chưa có corruption log.")
    else:
        st.caption(f"{log['input_rows']} → {log['output_rows']} rows, {log['operation_count']} operations")
        for op in log["operations"]:
            with st.expander(f"{op['type']} — {', '.join(op['paper_ids'])}"):
                col1, col2 = st.columns(2)
                col1.write("**Before**")
                col1.json(op["before"])
                col2.write("**After**")
                col2.json(op["after"])

    st.subheader("Reports")
    tab1, tab2 = st.tabs(["Phase 1 Report", "Corruption Report"])
    with tab1:
        if exists(settings.paths.baseline_report):
            st.markdown(settings.paths.baseline_report.read_text(encoding="utf-8"))
        else:
            st.info("Chưa có phase1_report.md.")
    with tab2:
        if exists(settings.paths.comparison_report):
            st.markdown(settings.paths.comparison_report.read_text(encoding="utf-8"))
        else:
            st.info("Chưa có corruption_report.md.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


PAGES = {
    "Overview": render_overview,
    "RAG Explorer": render_rag_explorer,
    "Evaluation": render_evaluation,
    "Data Quality & Freshness": render_quality,
    "Corruption & Reports": render_corruption_reports,
}


def main() -> None:
    st.set_page_config(page_title="RAG Pipeline Dashboard", layout="wide")
    settings = get_settings()

    if st.sidebar.button("🔄 Refresh data"):
        read_json_cached.clear()

    page = st.sidebar.radio("Page", list(PAGES.keys()))
    PAGES[page](settings)


if __name__ == "__main__":
    main()
