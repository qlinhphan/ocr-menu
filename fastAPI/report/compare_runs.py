from __future__ import annotations

import argparse
from pathlib import Path

from common import ensure_artifacts_dir, dump_json, load_json


MAIN_METRICS = [
    "field_accuracy_name",
    "field_accuracy_price",
    "field_accuracy_category",
    "item_recall",
    "item_precision",
    "hallucination_rate",
    "structure_correctness",
    "latency_ms",
    "auto_publish_acceptance",
    "auto_publish_accuracy",
]


def compare_runs(run_paths: list[Path]) -> dict:
    rows = []
    for run_path in run_paths:
        payload = load_json(run_path)
        metrics = payload.get("overall_metrics", {})
        rows.append(
            {
                "run_name": payload.get("run_name", run_path.stem),
                **{metric: metrics.get(metric, 0.0) for metric in MAIN_METRICS},
                "guardrail_threshold": payload.get("guardrail", {}).get("selected_threshold", 1.0),
            }
        )

    return {
        "runs": rows,
        "main_metrics": MAIN_METRICS,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", nargs="+", required=True, help="Benchmark JSON files")
    args = parser.parse_args()

    run_paths = [Path(path) for path in args.runs]
    comparison = compare_runs(run_paths)
    output_path = ensure_artifacts_dir() / "run_comparison.json"
    dump_json(output_path, comparison)
    print(f"Saved comparison to: {output_path}")


if __name__ == "__main__":
    main()
