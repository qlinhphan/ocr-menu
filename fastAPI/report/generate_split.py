from __future__ import annotations

import argparse
import random
from collections import defaultdict
from pathlib import Path

from common import CONFIGS_DIR, ensure_artifacts_dir, dump_json, load_json


def generate_split(seed: int, dev_ratio: float, min_labeled_per_group_for_test: int) -> dict:
    manifest = load_json(ensure_artifacts_dir() / "dataset_manifest.json")
    labeled_records = [record for record in manifest["records"] if record["has_label"]]

    grouped = defaultdict(list)
    for record in labeled_records:
        grouped[record["group"]].append(record)

    randomizer = random.Random(seed)
    dev_records = []
    test_records = []

    for group_name, records in grouped.items():
        shuffled = records[:]
        randomizer.shuffle(shuffled)
        if len(shuffled) <= min_labeled_per_group_for_test:
            test_count = max(1, len(shuffled) - 1)
        else:
            test_count = max(min_labeled_per_group_for_test, round(len(shuffled) * (1.0 - dev_ratio)))

        test_group = shuffled[:test_count]
        dev_group = shuffled[test_count:]
        test_records.extend(test_group)
        dev_records.extend(dev_group)

    return {
        "seed": seed,
        "dev_ratio": dev_ratio,
        "min_labeled_per_group_for_test": min_labeled_per_group_for_test,
        "dev_ids": sorted(record["id"] for record in dev_records),
        "test_ids": sorted(record["id"] for record in test_records),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default=str(CONFIGS_DIR / "default_split_config.json"),
        help="Path to split config JSON",
    )
    args = parser.parse_args()

    config = load_json(CONFIGS_DIR / Path(args.config).name if not Path(args.config).is_absolute() else Path(args.config))
    split = generate_split(
        seed=int(config["seed"]),
        dev_ratio=float(config["dev_ratio"]),
        min_labeled_per_group_for_test=int(config["min_labeled_per_group_for_test"]),
    )
    output_path = ensure_artifacts_dir() / "dataset_split.json"
    dump_json(output_path, split)
    print(f"Saved split to: {output_path}")


if __name__ == "__main__":
    main()
