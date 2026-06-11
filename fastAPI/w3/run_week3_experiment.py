from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

CURRENT_DIR = Path(__file__).resolve().parent
FASTAPI_DIR = CURRENT_DIR.parent
REPORT_DIR = FASTAPI_DIR / "report"
DATASET_IMAGES_DIR = FASTAPI_DIR / "dataset" / "images"
DATASET_LABELS_DIR = FASTAPI_DIR / "dataset" / "labels"
RULES_FILE = FASTAPI_DIR / "rules_response.md"

if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))
if str(REPORT_DIR) not in sys.path:
    sys.path.insert(0, str(REPORT_DIR))

from approach_multiview_preprocess import ocr_menu_multiview
from common import dump_json

load_dotenv(FASTAPI_DIR / ".env")


def load_rules() -> str:
    with RULES_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)
    return json.dumps(data, ensure_ascii=False, indent=2)


def convert_response_to_json(content: str) -> dict[str, Any]:
    fenced_match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)
    raw_json = fenced_match.group(1) if fenced_match else content.strip()
    parsed = json.loads(raw_json)
    if not isinstance(parsed, dict):
        raise ValueError("Model khong tra ve object JSON hop le")
    return parsed


def build_model() -> ChatOpenAI:
    model_name = os.getenv("MODEL_CHAT")
    base_url = os.getenv("BASE_URL")

    if not model_name:
        raise RuntimeError("Thieu bien moi truong MODEL_CHAT trong fastAPI/.env")

    return ChatOpenAI(model=model_name, base_url=base_url)


def structure_menu_from_ocr(model: ChatOpenAI, rules: str, ocr_result: list[dict[str, Any]]) -> dict[str, Any]:
    messages = [
        SystemMessage(
            content=(
                "Ban la tro ly AI chuyen ket qua OCR menu thanh JSON co cau truc chinh xac. "
                "Uu tien bang chung thi giac tu OCR, box, cot va bo cuc thay vi suy doan theo ten mon."
            )
        ),
        HumanMessage(
            content=(
                "Hay chuyen doi ket qua OCR sau thanh JSON dung schema.\n\n"
                f"Ket qua OCR:\n{json.dumps(ocr_result, ensure_ascii=False)}\n\n"
                f"Schema/JSON mau:\n{rules}\n\n"
                "Bat buoc:\n"
                "- categories la mang dong.\n"
                "- Tach dung category neu menu co nhieu tieu de nhom.\n"
                "- Giu thu tu category va item theo bo cuc menu.\n"
                "- Khong gop mon theo suy luan ngu nghia neu box/layout cho thay khac.\n"
                "- Chi tra ve duy nhat JSON hop le dung schema."
            )
        ),
    ]
    response = model.invoke(messages)
    return convert_response_to_json(response.content)


def iter_labeled_samples(limit: int | None = None) -> list[tuple[str, str, Path]]:
    samples: list[tuple[str, str, Path]] = []
    for label_path in sorted(DATASET_LABELS_DIR.rglob("*.json")):
        group_name = label_path.parent.name
        stem = label_path.stem
        image_path = resolve_image_path(group_name, stem)
        if image_path:
            samples.append((group_name, stem, image_path))
        if limit is not None and len(samples) >= limit:
            break
    return samples


def resolve_image_path(group_name: str, stem: str) -> Path | None:
    group_dir = DATASET_IMAGES_DIR / group_name
    for extension in (".png", ".jpg", ".jpeg", ".webp"):
        candidate = group_dir / f"{stem}{extension}"
        if candidate.exists():
            return candidate
    return None


def build_prediction_meta(run_name: str, ocr_meta: dict[str, Any], total_latency_ms: float) -> dict[str, Any]:
    return {
        "method": run_name,
        "method_family": "ocr_multiview_preprocess_llm",
        "model_version": os.getenv("MODEL_CHAT", "unknown"),
        "prompt_version": "w3_multiview_prompt_v1",
        "schema_version": "schema_v1",
        "confidence": 0.75,
        "latency_ms": round(total_latency_ms, 2),
        "preprocessing": {
            "resize_long_side": 1800,
            "deskew": True,
            "clahe": True,
            "denoise": True,
            "adaptive_threshold": True,
            "views": ["raw", "enhanced", "binary"],
        },
        "ocr_debug": ocr_meta,
    }


def ensure_prediction_shape(prediction: dict[str, Any]) -> dict[str, Any]:
    categories = prediction.get("categories")
    if not isinstance(categories, list):
        prediction["categories"] = []
    return prediction


def run_experiment(
    output_root: Path,
    run_name: str,
    limit: int | None = None,
    save_debug_images: bool = False,
    continue_on_error: bool = True,
) -> None:
    model = build_model()
    rules = load_rules()
    samples = iter_labeled_samples(limit=limit)
    debug_dir = CURRENT_DIR / "artifacts" / run_name

    for index, (group_name, stem, image_path) in enumerate(samples, start=1):
        started_at = time.time()
        prediction_path = output_root / group_name / f"{stem}.json"
        debug_image_path = debug_dir / f"{group_name}_{stem}_ocr.png" if save_debug_images else None
        preprocess_dir = debug_dir / "preprocessed" if save_debug_images else None

        print(f"[{index}/{len(samples)}] Processing {group_name}/{stem}")

        try:
            ocr_payload = ocr_menu_multiview(
                img_path=image_path,
                output_image_path=str(debug_image_path) if debug_image_path else None,
                save_preprocessed_dir=str(preprocess_dir) if preprocess_dir else None,
            )
            prediction = structure_menu_from_ocr(model, rules, ocr_payload["lines"])
            prediction = ensure_prediction_shape(prediction)
            prediction["_meta"] = build_prediction_meta(
                run_name=run_name,
                ocr_meta=ocr_payload["meta"],
                total_latency_ms=(time.time() - started_at) * 1000.0,
            )
        except Exception as exc:
            if not continue_on_error:
                raise
            prediction = {
                "categories": [],
                "_meta": {
                    "method": run_name,
                    "method_family": "ocr_multiview_preprocess_llm",
                    "latency_ms": round((time.time() - started_at) * 1000.0, 2),
                    "error": str(exc),
                },
            }

        dump_json(prediction_path, prediction)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-root",
        default=str(FASTAPI_DIR / "report" / "predictions" / "w3_multiview_preprocess"),
        help="Folder ghi prediction JSON de benchmark",
    )
    parser.add_argument("--run-name", default="w3_multiview_preprocess")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--save-debug-images", action="store_true")
    parser.add_argument("--fail-fast", action="store_true")
    args = parser.parse_args()

    run_experiment(
        output_root=Path(args.output_root),
        run_name=args.run_name,
        limit=args.limit,
        save_debug_images=args.save_debug_images,
        continue_on_error=not args.fail_fast,
    )


if __name__ == "__main__":
    main()

