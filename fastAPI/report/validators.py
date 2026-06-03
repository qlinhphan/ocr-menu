from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ValidationIssue:
    path: str
    message: str


def validate_menu_schema(data: Any) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    if not isinstance(data, dict):
        return [ValidationIssue(path="$", message="Root must be an object")]

    allowed_root = {"categories", "_meta"}
    for key in data:
        if key not in allowed_root:
            issues.append(ValidationIssue(path=f"$.{key}", message="Unexpected root field"))

    categories = data.get("categories")
    if not isinstance(categories, list):
        issues.append(ValidationIssue(path="$.categories", message="categories must be a list"))
        return issues

    for category_index, category in enumerate(categories):
        category_path = f"$.categories[{category_index}]"
        if not isinstance(category, dict):
            issues.append(ValidationIssue(path=category_path, message="Category must be an object"))
            continue

        for key in category:
            if key not in {"name", "items"}:
                issues.append(ValidationIssue(path=f"{category_path}.{key}", message="Unexpected category field"))

        if not isinstance(category.get("name"), str):
            issues.append(ValidationIssue(path=f"{category_path}.name", message="Category name must be a string"))

        items = category.get("items")
        if not isinstance(items, list):
            issues.append(ValidationIssue(path=f"{category_path}.items", message="items must be a list"))
            continue

        for item_index, item in enumerate(items):
            item_path = f"{category_path}.items[{item_index}]"
            if not isinstance(item, dict):
                issues.append(ValidationIssue(path=item_path, message="Item must be an object"))
                continue

            for key in item:
                if key not in {"name", "descriptions"}:
                    issues.append(ValidationIssue(path=f"{item_path}.{key}", message="Unexpected item field"))

            if not isinstance(item.get("name"), str):
                issues.append(ValidationIssue(path=f"{item_path}.name", message="Item name must be a string"))

            descriptions = item.get("descriptions")
            if not isinstance(descriptions, list):
                issues.append(ValidationIssue(path=f"{item_path}.descriptions", message="descriptions must be a list"))
                continue

            for desc_index, desc in enumerate(descriptions):
                desc_path = f"{item_path}.descriptions[{desc_index}]"
                if not isinstance(desc, dict):
                    issues.append(ValidationIssue(path=desc_path, message="Description must be an object"))
                    continue

                for key in desc:
                    if key not in {"size", "price", "optional", "description"}:
                        issues.append(ValidationIssue(path=f"{desc_path}.{key}", message="Unexpected description field"))

                price = desc.get("price")
                if not isinstance(price, int) or isinstance(price, bool) or price < 0:
                    issues.append(ValidationIssue(path=f"{desc_path}.price", message="price must be a non-negative integer"))

                for nullable_text_field in ("size", "optional", "description"):
                    value = desc.get(nullable_text_field)
                    if value is not None and not isinstance(value, str):
                        issues.append(
                            ValidationIssue(
                                path=f"{desc_path}.{nullable_text_field}",
                                message=f"{nullable_text_field} must be a string or null",
                            )
                        )

    return issues
