from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from normalization import fuzzy_name_match, normalize_price, normalize_text


@dataclass
class FlatItem:
    category_name: str
    item_name: str
    price: int | None


def flatten_menu(menu: dict[str, Any]) -> list[FlatItem]:
    flat_items: list[FlatItem] = []
    for category in menu.get("categories", []):
        category_name = category.get("name", "")
        for item in category.get("items", []):
            item_name = item.get("name", "")
            descriptions = item.get("descriptions", [])
            if not descriptions:
                flat_items.append(FlatItem(category_name=category_name, item_name=item_name, price=None))
                continue
            for desc in descriptions:
                flat_items.append(
                    FlatItem(
                        category_name=category_name,
                        item_name=item_name,
                        price=normalize_price(desc.get("price")),
                    )
                )
    return flat_items


def match_items(gt_items: list[FlatItem], pred_items: list[FlatItem]) -> tuple[list[tuple[int, int]], list[int], list[int]]:
    matches: list[tuple[int, int]] = []
    used_pred: set[int] = set()

    for gt_index, gt_item in enumerate(gt_items):
        best_pred_index = None
        best_score = -1
        for pred_index, pred_item in enumerate(pred_items):
            if pred_index in used_pred:
                continue

            score = 0
            if fuzzy_name_match(gt_item.item_name, pred_item.item_name):
                score += 2
            if gt_item.price is not None and pred_item.price is not None and gt_item.price == pred_item.price:
                score += 2
            if normalize_text(gt_item.category_name) == normalize_text(pred_item.category_name):
                score += 1

            if score > best_score:
                best_score = score
                best_pred_index = pred_index

        if best_pred_index is not None and best_score >= 2:
            used_pred.add(best_pred_index)
            matches.append((gt_index, best_pred_index))

    unmatched_gt = [index for index in range(len(gt_items)) if index not in {gt for gt, _ in matches}]
    unmatched_pred = [index for index in range(len(pred_items)) if index not in used_pred]
    return matches, unmatched_gt, unmatched_pred


def safe_divide(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def structure_correctness(gt_menu: dict[str, Any], pred_menu: dict[str, Any]) -> float:
    gt_categories = [normalize_text(category.get("name", "")) for category in gt_menu.get("categories", [])]
    pred_categories = [normalize_text(category.get("name", "")) for category in pred_menu.get("categories", [])]
    if not gt_categories and not pred_categories:
        return 1.0
    exact_prefix_hits = sum(1 for left, right in zip(gt_categories, pred_categories) if left == right)
    return safe_divide(exact_prefix_hits, max(len(gt_categories), len(pred_categories)))


def compute_sample_metrics(gt_menu: dict[str, Any], pred_menu: dict[str, Any]) -> dict[str, Any]:
    gt_items = flatten_menu(gt_menu)
    pred_items = flatten_menu(pred_menu)
    matches, unmatched_gt, unmatched_pred = match_items(gt_items, pred_items)

    name_hits = 0
    price_hits = 0
    category_hits = 0

    for gt_index, pred_index in matches:
        gt_item = gt_items[gt_index]
        pred_item = pred_items[pred_index]
        if fuzzy_name_match(gt_item.item_name, pred_item.item_name):
            name_hits += 1
        if gt_item.price == pred_item.price and gt_item.price is not None:
            price_hits += 1
        if normalize_text(gt_item.category_name) == normalize_text(pred_item.category_name):
            category_hits += 1

    matched_count = len(matches)
    gt_count = len(gt_items)
    pred_count = len(pred_items)
    structure_score = structure_correctness(gt_menu, pred_menu)

    return {
        "gt_count": gt_count,
        "pred_count": pred_count,
        "matched_count": matched_count,
        "field_accuracy_name": safe_divide(name_hits, gt_count),
        "field_accuracy_price": safe_divide(price_hits, gt_count),
        "field_accuracy_category": safe_divide(category_hits, gt_count),
        "item_recall": safe_divide(matched_count, gt_count),
        "item_precision": safe_divide(matched_count, pred_count),
        "hallucination_rate": safe_divide(len(unmatched_pred), pred_count),
        "structure_correctness": structure_score,
        "unmatched_gt_indices": unmatched_gt,
        "unmatched_pred_indices": unmatched_pred,
    }


def aggregate_sample_metrics(samples: list[dict[str, Any]]) -> dict[str, float]:
    if not samples:
        return {
            "field_accuracy_name": 0.0,
            "field_accuracy_price": 0.0,
            "field_accuracy_category": 0.0,
            "item_recall": 0.0,
            "item_precision": 0.0,
            "hallucination_rate": 0.0,
            "structure_correctness": 0.0,
            "latency_ms": 0.0,
            "auto_publish_acceptance": 0.0,
            "auto_publish_accuracy": 0.0,
        }

    metric_keys = [
        "field_accuracy_name",
        "field_accuracy_price",
        "field_accuracy_category",
        "item_recall",
        "item_precision",
        "hallucination_rate",
        "structure_correctness",
        "latency_ms",
    ]
    result: dict[str, float] = {}
    for key in metric_keys:
        result[key] = sum(float(sample.get(key, 0.0)) for sample in samples) / len(samples)

    accepted_samples = [sample for sample in samples if sample.get("auto_publish")]
    result["auto_publish_acceptance"] = safe_divide(len(accepted_samples), len(samples))
    result["auto_publish_accuracy"] = (
        sum(float(sample.get("item_precision", 0.0)) for sample in accepted_samples) / len(accepted_samples)
        if accepted_samples
        else 0.0
    )
    return result
