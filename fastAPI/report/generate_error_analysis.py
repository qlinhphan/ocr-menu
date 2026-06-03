from __future__ import annotations

import argparse
from pathlib import Path

from common import ensure_artifacts_dir, load_json


def build_error_analysis(benchmark_path: Path) -> str:
    benchmark = load_json(benchmark_path)
    samples = benchmark.get("samples", [])

    worst_recall = sorted(samples, key=lambda sample: (sample.get("item_recall", 0.0), sample.get("item_precision", 0.0)))[:10]
    worst_precision = sorted(samples, key=lambda sample: sample.get("item_precision", 0.0))[:10]
    most_validation_errors = sorted(samples, key=lambda sample: sample.get("validation_error_count", 0), reverse=True)[:10]

    lines = ["# Error Analysis", ""]
    lines.append("## Worst recall samples")
    lines.append("")
    for sample in worst_recall:
        lines.append(
            f"- {sample['sample_id']}: recall={sample.get('item_recall', 0.0):.3f}, "
            f"precision={sample.get('item_precision', 0.0):.3f}, "
            f"validation_errors={sample.get('validation_error_count', 0)}"
        )

    lines.append("")
    lines.append("## Worst precision samples")
    lines.append("")
    for sample in worst_precision:
        lines.append(
            f"- {sample['sample_id']}: precision={sample.get('item_precision', 0.0):.3f}, "
            f"hallucination={sample.get('hallucination_rate', 0.0):.3f}, "
            f"group={sample.get('group', '')}"
        )

    lines.append("")
    lines.append("## Most validation errors")
    lines.append("")
    for sample in most_validation_errors:
        lines.append(
            f"- {sample['sample_id']}: validation_errors={sample.get('validation_error_count', 0)}, "
            f"prediction_path={sample.get('prediction_path')}"
        )

    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", required=True)
    args = parser.parse_args()

    benchmark_path = Path(args.benchmark)
    report_text = build_error_analysis(benchmark_path)
    output_path = ensure_artifacts_dir() / f"error_analysis_{benchmark_path.stem}.md"
    output_path.write_text(report_text, encoding="utf-8")
    print(f"Saved error analysis to: {output_path}")


if __name__ == "__main__":
    main()
