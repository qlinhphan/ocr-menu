from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPORT_DIR = Path(__file__).resolve().parent
FASTAPI_DIR = REPORT_DIR.parent
DATASET_DIR = FASTAPI_DIR / "dataset"
IMAGES_DIR = DATASET_DIR / "images"
LABELS_DIR = DATASET_DIR / "labels"
SCHEMA_PATH = DATASET_DIR / "schema_v1.json"
ARTIFACTS_DIR = REPORT_DIR / "artifacts"
CONFIGS_DIR = REPORT_DIR / "configs"
TEMPLATES_DIR = REPORT_DIR / "templates"


def ensure_artifacts_dir() -> Path:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    return ARTIFACTS_DIR


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def dump_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def rel_to_fastapi(path: Path) -> str:
    return path.resolve().relative_to(FASTAPI_DIR.resolve()).as_posix()

