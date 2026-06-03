from __future__ import annotations

from pathlib import Path

from common import IMAGES_DIR, LABELS_DIR, ensure_artifacts_dir, dump_json, rel_to_fastapi


VALID_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def build_manifest() -> dict:
    records = []
    for image_path in sorted(path for path in IMAGES_DIR.rglob("*") if path.is_file() and path.suffix.lower() in VALID_IMAGE_EXTENSIONS):
        group_name = image_path.parent.name
        label_path = LABELS_DIR / group_name / f"{image_path.stem}.json"
        records.append(
            {
                "id": f"{group_name}/{image_path.stem}",
                "group": group_name,
                "image_path": rel_to_fastapi(image_path),
                "label_path": rel_to_fastapi(label_path) if label_path.exists() else None,
                "has_label": label_path.exists(),
            }
        )

    per_group = {}
    for record in records:
        group_stats = per_group.setdefault(record["group"], {"images": 0, "labels": 0})
        group_stats["images"] += 1
        if record["has_label"]:
            group_stats["labels"] += 1

    return {
        "dataset_root": "dataset",
        "total_images": len(records),
        "total_labeled_images": sum(1 for record in records if record["has_label"]),
        "groups": per_group,
        "records": records,
    }


def main() -> None:
    artifacts_dir = ensure_artifacts_dir()
    manifest = build_manifest()
    output_path = artifacts_dir / "dataset_manifest.json"
    dump_json(output_path, manifest)
    print(f"Saved dataset manifest to: {output_path}")


if __name__ == "__main__":
    main()
