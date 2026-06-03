from __future__ import annotations

import argparse
from pathlib import Path

from common import TEMPLATES_DIR, ensure_artifacts_dir, load_json


def format_float(value: float) -> str:
    return f"{value:.3f}"


def build_final_report(comparison_path: Path) -> str:
    template = (TEMPLATES_DIR / "final_report_template.md").read_text(encoding="utf-8")
    comparison = load_json(comparison_path)
    rows = comparison.get("runs", [])

    leaderboard_lines = []
    for row in rows:
        leaderboard_lines.append(
            "- "
            + row["run_name"]
            + f": recall={format_float(row.get('item_recall', 0.0))}, "
            + f"precision={format_float(row.get('item_precision', 0.0))}, "
            + f"hallucination={format_float(row.get('hallucination_rate', 0.0))}, "
            + f"auto_publish_acceptance={format_float(row.get('auto_publish_acceptance', 0.0))}"
        )

    report = template
    report += "\n\n## Auto-generated comparison\n\n"
    report += "\n".join(leaderboard_lines) if leaderboard_lines else "- Chua co run nao de so sanh"
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--comparison", required=True)
    args = parser.parse_args()

    comparison_path = Path(args.comparison)
    report_text = build_final_report(comparison_path=comparison_path)
    output_path = ensure_artifacts_dir() / "final_report.md"
    output_path.write_text(report_text, encoding="utf-8")
    print(f"Saved final report to: {output_path}")


if __name__ == "__main__":
    main()
