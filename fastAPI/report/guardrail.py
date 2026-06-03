from __future__ import annotations

from typing import Any

from metrics import safe_divide


def heuristic_confidence(menu: dict[str, Any], validation_error_count: int) -> float:
    categories = menu.get("categories", [])
    item_count = 0
    description_count = 0
    missing_price_count = 0
    empty_name_count = 0

    for category in categories:
        if not category.get("name"):
            empty_name_count += 1
        for item in category.get("items", []):
            item_count += 1
            if not item.get("name"):
                empty_name_count += 1
            descriptions = item.get("descriptions", [])
            description_count += len(descriptions)
            for desc in descriptions:
                if desc.get("price") in (None, ""):
                    missing_price_count += 1

    if item_count == 0:
        return 0.0

    price_penalty = safe_divide(missing_price_count, max(description_count, 1))
    name_penalty = safe_divide(empty_name_count, item_count + len(categories))
    validation_penalty = min(1.0, validation_error_count / 10.0)
    confidence = 1.0 - (0.45 * price_penalty + 0.35 * name_penalty + 0.20 * validation_penalty)
    return max(0.0, min(1.0, confidence))


def calibrate_threshold(samples: list[dict[str, Any]], min_precision: float = 0.95) -> dict[str, Any]:
    thresholds = [round(step / 100.0, 2) for step in range(0, 101, 5)]
    curve: list[dict[str, float]] = []
    best_threshold = 1.0
    best_coverage = -1.0
    best_accuracy = 0.0

    for threshold in thresholds:
        accepted = [sample for sample in samples if float(sample.get("confidence", 0.0)) >= threshold]
        coverage = safe_divide(len(accepted), len(samples))
        accuracy = (
            sum(float(sample.get("item_precision", 0.0)) for sample in accepted) / len(accepted)
            if accepted
            else 0.0
        )
        curve.append({"threshold": threshold, "coverage": coverage, "accuracy": accuracy})
        if accuracy >= min_precision and coverage > best_coverage:
            best_threshold = threshold
            best_coverage = coverage
            best_accuracy = accuracy

    if best_coverage < 0:
        best_threshold = 1.0
        best_coverage = 0.0
        best_accuracy = 0.0

    return {
        "selected_threshold": best_threshold,
        "selected_coverage": best_coverage,
        "selected_accuracy": best_accuracy,
        "curve": curve,
        "min_precision_target": min_precision,
    }
