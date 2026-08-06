from __future__ import annotations

import sys

import pandas as pd

from core.config import load_settings, normalized_provider, require_llm_credentials
from core.utils import read_json
from ingestion.cleaning import validate_clean_dataframe
from retrieval.agent import build_agent, run_agent_question
from retrieval.index import LocalEmbeddingIndex

PLACEHOLDER_QUERY = "retrieval augmented generation evaluation"  # SMOKE-TEST PLACEHOLDER


def _load_clean_dataframe(settings) -> pd.DataFrame | None:
    if settings.paths.clean_csv.exists():
        return pd.read_csv(settings.paths.clean_csv)
    if settings.paths.clean_json.exists():
        return pd.DataFrame(read_json(settings.paths.clean_json))
    return None


def main() -> int:
    settings = load_settings()

    df = _load_clean_dataframe(settings)
    if df is None:
        print(
            f"[NOT READY] Neither {settings.paths.clean_csv} nor "
            f"{settings.paths.clean_json} exists yet - ask the clean-role teammate "
            "to finish data/clean/. Exiting cleanly."
        )
        return 0

    errors = validate_clean_dataframe(df)
    if errors:
        print("[FAIL] clean dataframe violates the index contract:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"[OK] {len(df)} rows loaded, contract valid.")
    for _, row in df.head(3).iterrows():
        text = str(row["text_for_embedding"])
        print(f"  paper_id={row['paper_id']!r} text_for_embedding[:160]={text[:160]!r}")

    throwaway_path = settings.paths.embeddings_json.parent / "_smoke_test.json"
    index = LocalEmbeddingIndex.build(df, settings, embeddings_output_path=throwaway_path)
    print(
        f"[OK] built throwaway collection '{index.collection_name}' "
        f"(chroma dir: {index.persist_path})"
    )

    results = index.search(PLACEHOLDER_QUERY, top_k=3)
    print(f"[search] query={PLACEHOLDER_QUERY!r} -> {len(results)} hits")
    for r in results:
        print(f"  score={r.score:.3f} paper_id={r.paper_id} title={r.title}")

    real_id = str(df.iloc[0]["paper_id"])
    hit = index.lookup(real_id)
    print(f"[lookup] paper_id={real_id!r} -> {'found' if hit else 'NOT FOUND'}")

    try:
        require_llm_credentials(settings)
        agent = build_agent(settings, index)
        answer = run_agent_question(agent, "What papers are in the corpus about RAG?")
        print(f"[agent:{normalized_provider(settings)}] {answer[:300]}")
    except RuntimeError as exc:
        print(f"[skipped] agent step: no LLM credentials configured ({exc})")

    print("=== SMOKE TEST: PASS ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
