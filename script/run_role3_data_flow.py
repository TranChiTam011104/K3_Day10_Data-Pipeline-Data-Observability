from __future__ import annotations

import json

from core.config import load_settings
from ingestion.role3_flow import run_role3_data_flow


def main() -> None:
    summary = run_role3_data_flow(load_settings())
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
