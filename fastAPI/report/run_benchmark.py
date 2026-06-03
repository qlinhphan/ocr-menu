from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import Any

from common import FASTAPI_DIR, LABELS_DIR, ensure_artifacts_dir, dump_json, load_json
from guardrail import calibrate_threshold, heuristic_confidence
from metrics import aggregate_sample_metrics, compute_sample_metrics
from validators import validate_menu_schema


def resolve_prediction_path(predictions_root: Path, sample_id: str) -> Path:
    group_name, stem = sample_id.split("/")
    return predictions_root / group_name / f"{stem}.json"


def load_prediction(prediction_path: Path) -> dict[str, Any] | None:
    if not prediction_path.exists():
        return None
    data = load_json(prediction_path)
    if not isinstance(data, dict):
        return None
    return data


def run_benchmark(predictions_root: Path, run_name: str, precision_target: float) -> dict[str, Any]:
    artifacts_dir = ensure_artifacts_dir()
    split = load_json(artifacts_dir / "dataset_split.json")
    manifest = load_json(artifacts_dir / "dataset_manifest.json")
    labeled_records = {record["id"]: record for record in manifest["records"] if record["has_label"]}

    samples = []
    started_at = time.time()

    for sample_id in split["test_ids"]:
        record = labeled_records[sample_id]
        group_name, stem = sample_id.split("/")
        gt_path = LABELS_DIR / group_name / f"{stem}.json"
        gt_menu = load_json(gt_path)
        prediction_path = resolve_prediction_path(predictions_root, sample_id)
        pred_menu = load_prediction(prediction_path)

        if pred_menu is None:
            pred_menu = {"categories": []}

        validation_issues = validate_menu_schema(pred_menu)
        sample_metrics = compute_sample_metrics(gt_menu, pred_menu)
        meta = pred_menu.get("_meta", {}) if isinstance(pred_menu.get("_meta", {}), dict) else {}
        confidence = meta.get("confidence")
        if confidence is None:
            confidence = heuristic_confidence(pred_menu, len(validation_issues))
        latency_ms = float(meta.get("latency_ms", 0.0))

        samples.append(
            {
                "sample_id": sample_id,
                "group": record["group"],
                "ground_truth_path": record["label_path"],
                "prediction_path": str(prediction_path.relative_to(FASTAPI_DIR)) if prediction_path.exists() else None,
                "validation_error_count": len(validation_issues),
                "validation_issues": [issue.__dict__ for issue in validation_issues],
                "confidence": float(confidence),
                "latency_ms": latency_ms,
                **sample_metrics,
                "meta": meta,
            }
        )

    guardrail = calibrate_threshold(samples, min_precision=precision_target)
    threshold = float(guardrail["selected_threshold"])
    for sample in samples:
        sample["auto_publish"] = sample["confidence"] >= threshold

    overall_metrics = aggregate_sample_metrics(samples)
    by_group: dict[str, list[dict[str, Any]]] = {}
    for sample in samples:
        by_group.setdefault(sample["group"], []).append(sample)

    group_metrics = {group_name: aggregate_sample_metrics(group_samples) for group_name, group_samples in by_group.items()}
    elapsed_ms = (time.time() - started_at) * 1000.0

    result = {
        "run_name": run_name,
        "predictions_root": str(predictions_root),
        "precision_target": precision_target,
        "sample_count": len(samples),
        "overall_metrics": overall_metrics,
        "group_metrics": group_metrics,
        "guardrail": guardrail,
        "runtime_ms": elapsed_ms,
        "samples": samples,
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", required=True, help="Prediction root directory")
    parser.add_argument("--run-name", required=True, help="Name for this benchmark run")
    parser.add_argument("--precision-target", type=float, default=0.95)
    args = parser.parse_args()

    predictions_root = Path(args.predictions)
    result = run_benchmark(predictions_root=predictions_root, run_name=args.run_name, precision_target=args.precision_target)
    output_path = ensure_artifacts_dir() / f"benchmark_{args.run_name}.json"
    dump_json(output_path, result)
    print(f"Saved benchmark to: {output_path}")


if __name__ == "__main__":
    main()
