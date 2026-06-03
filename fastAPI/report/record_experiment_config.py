from __future__ import annotations

import argparse
import platform
from datetime import datetime, timezone
from pathlib import Path

from common import ensure_artifacts_dir, dump_json, load_json


def record_config(config_path: Path) -> dict:
    config = load_json(config_path)
    return {
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "config": config,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="JSON metadata config")
    parser.add_argument("--output-name", default="experiment_config")
    args = parser.parse_args()

    payload = record_config(Path(args.config))
    output_path = ensure_artifacts_dir() / f"{args.output_name}.json"
    dump_json(output_path, payload)
    print(f"Saved experiment config to: {output_path}")


if __name__ == "__main__":
    main()
