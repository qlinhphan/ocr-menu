from __future__ import annotations

import argparse
from pathlib import Path

from common import TEMPLATES_DIR, ensure_artifacts_dir, load_json


def format_float(value: float) -> str:
    return f"{value:.3f}"


def build_weekly_report(benchmark_path: Path, week: str, method_name: str) -> str:
    template = (TEMPLATES_DIR / "weekly_report_template.md").read_text(encoding="utf-8")
    benchmark = load_json(benchmark_path)
    overall = benchmark.get("overall_metrics", {})
    guardrail = benchmark.get("guardrail", {})

    metrics_lines = [
        f"- Name accuracy: {format_float(overall.get('field_accuracy_name', 0.0))}",
        f"- Price accuracy: {format_float(overall.get('field_accuracy_price', 0.0))}",
        f"- Category accuracy: {format_float(overall.get('field_accuracy_category', 0.0))}",
        f"- Item recall: {format_float(overall.get('item_recall', 0.0))}",
        f"- Item precision: {format_float(overall.get('item_precision', 0.0))}",
        f"- Hallucination rate: {format_float(overall.get('hallucination_rate', 0.0))}",
        f"- Structure correctness: {format_float(overall.get('structure_correctness', 0.0))}",
        f"- Avg latency ms: {format_float(overall.get('latency_ms', 0.0))}",
        f"- Auto-publish acceptance: {format_float(overall.get('auto_publish_acceptance', 0.0))}",
        f"- Auto-publish accuracy: {format_float(overall.get('auto_publish_accuracy', 0.0))}",
        f"- Guardrail threshold: {format_float(guardrail.get('selected_threshold', 1.0))}",
    ]

    difficult_groups = benchmark.get("group_metrics", {})
    group_lines = [f"- {group}: recall={format_float(metrics.get('item_recall', 0.0))}, precision={format_float(metrics.get('item_precision', 0.0))}" for group, metrics in difficult_groups.items()]

    report = template.replace("{{week}}", week)
    report += "\n\n## Auto-generated summary\n\n"
    report += f"- Method: {method_name}\n"
    report += f"- Sample count: {benchmark.get('sample_count', 0)}\n"
    report += "\n".join(metrics_lines) + "\n\n"
    report += "## Theo nhom anh kho\n\n"
    report += "\n".join(group_lines) if group_lines else "- Chua co du lieu theo nhom\n"
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", required=True)
    parser.add_argument("--week", required=True)
    parser.add_argument("--method-name", required=True)
    args = parser.parse_args()

    benchmark_path = Path(args.benchmark)
    report_text = build_weekly_report(benchmark_path=benchmark_path, week=args.week, method_name=args.method_name)
    output_path = ensure_artifacts_dir() / f"weekly_report_{args.week}_{args.method_name}.md"
    output_path.write_text(report_text, encoding="utf-8")
    print(f"Saved weekly report to: {output_path}")


if __name__ == "__main__":
    main()
