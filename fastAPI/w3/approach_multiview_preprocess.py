from __future__ import annotations

import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageDraw
from paddleocr import PaddleOCR
from vietocr.tool.config import Cfg
from vietocr.tool.predictor import Predictor

CURRENT_DIR = Path(__file__).resolve().parent
FASTAPI_DIR = CURRENT_DIR.parent

if str(FASTAPI_DIR) not in sys.path:
    sys.path.insert(0, str(FASTAPI_DIR))

from run import four_point_transform, load_unicode_font, safe_log


@dataclass
class OCRCandidate:
    name: str
    image: np.ndarray
    detector_result: list[Any]
    score: float


def resize_long_side(image: np.ndarray, target_long_side: int = 1800) -> np.ndarray:
    height, width = image.shape[:2]
    long_side = max(height, width)
    if long_side <= target_long_side:
        return image.copy()

    scale = target_long_side / float(long_side)
    new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
    return cv2.resize(image, new_size, interpolation=cv2.INTER_CUBIC)


def estimate_skew_angle(binary_inverse: np.ndarray) -> float:
    coords = np.column_stack(np.where(binary_inverse > 0))
    if coords.shape[0] < 100:
        return 0.0

    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    return float(angle)


def rotate_image(image: np.ndarray, angle: float) -> np.ndarray:
    if abs(angle) < 0.3:
        return image.copy()

    height, width = image.shape[:2]
    center = (width // 2, height // 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(
        image,
        matrix,
        (width, height),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )


def build_preprocessed_views(image: np.ndarray) -> dict[str, np.ndarray]:
    resized = resize_long_side(image)
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

    if float(np.mean(gray)) < 120.0:
        gray = cv2.bitwise_not(gray)

    denoised = cv2.fastNlMeansDenoising(gray, h=7)
    clahe = cv2.createCLAHE(clipLimit=2.2, tileGridSize=(8, 8)).apply(denoised)

    blur = cv2.GaussianBlur(clahe, (0, 0), 3)
    sharpened = cv2.addWeighted(clahe, 1.6, blur, -0.6, 0)

    binary_seed = cv2.adaptiveThreshold(
        sharpened,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        15,
    )
    angle = estimate_skew_angle(cv2.bitwise_not(binary_seed))
    aligned_gray = rotate_image(sharpened, angle)

    binary = cv2.adaptiveThreshold(
        aligned_gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        15,
    )
    kernel = np.ones((2, 2), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

    enhanced_bgr = cv2.cvtColor(aligned_gray, cv2.COLOR_GRAY2BGR)
    binary_bgr = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)

    return {
        "raw": resized,
        "enhanced": enhanced_bgr,
        "binary": binary_bgr,
    }


def run_detector_on_image(detector: PaddleOCR, image: np.ndarray) -> list[Any]:
    temp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
            temp_path = temp_file.name
        cv2.imwrite(temp_path, image)
        result = detector.ocr(temp_path)
        return result[0] if result and result[0] else []
    finally:
        if temp_path:
            try:
                Path(temp_path).unlink(missing_ok=True)
            except OSError:
                pass


def score_detector_output(lines: list[Any]) -> float:
    if not lines:
        return 0.0

    confidence_values: list[float] = []
    total_area = 0.0

    for line in lines:
        box = np.array(line[0], dtype=np.float32)
        total_area += abs(cv2.contourArea(box.astype(np.int32)))

        if len(line) > 1 and isinstance(line[1], (list, tuple)) and len(line[1]) > 1:
            try:
                confidence_values.append(float(line[1][1]))
            except (TypeError, ValueError):
                pass

    avg_confidence = sum(confidence_values) / len(confidence_values) if confidence_values else 0.0
    normalized_area = min(total_area / 1_000_000.0, 3.0)
    return (len(lines) * 2.0) + avg_confidence + normalized_area


def select_best_candidate(detector: PaddleOCR, image: np.ndarray) -> tuple[OCRCandidate, dict[str, float]]:
    views = build_preprocessed_views(image)
    scored_candidates: list[OCRCandidate] = []
    candidate_scores: dict[str, float] = {}

    for name, view_image in views.items():
        detector_result = run_detector_on_image(detector, view_image)
        score = score_detector_output(detector_result)
        candidate_scores[name] = score
        scored_candidates.append(
            OCRCandidate(
                name=name,
                image=view_image,
                detector_result=detector_result,
                score=score,
            )
        )

    scored_candidates.sort(key=lambda candidate: candidate.score, reverse=True)
    return scored_candidates[0], candidate_scores


def build_ocr_components() -> tuple[PaddleOCR, Predictor]:
    detector = PaddleOCR(use_angle_cls=True, lang="vi")

    config = Cfg.load_config_from_name("vgg_transformer")
    config["device"] = "cpu"
    recognizer = Predictor(config)

    return detector, recognizer


def draw_debug_image(image: np.ndarray, ocr_lines: list[dict[str, Any]], output_image_path: str) -> None:
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(rgb_image)
    drawer = ImageDraw.Draw(pil_image)
    font = load_unicode_font(size=20)

    for line in ocr_lines:
        box = np.array(line["box"], dtype=np.int32)
        drawer.line([tuple(point) for point in box] + [tuple(box[0])], fill=(0, 255, 0), width=2)
        x = int(box[0][0])
        y = int(box[0][1])
        drawer.text((x, max(0, y - 24)), line["text"], font=font, fill=(255, 0, 0))

    output_path = Path(output_image_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    debug_bgr = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    cv2.imwrite(str(output_path), debug_bgr)


def ocr_menu_multiview(
    img_path: str | Path,
    output_image_path: str | None = None,
    save_preprocessed_dir: str | Path | None = None,
) -> dict[str, Any]:
    started_at = time.time()
    detector, recognizer = build_ocr_components()

    image_path = Path(img_path)
    image = cv2.imread(str(image_path))
    if image is None:
        raise FileNotFoundError(f"Khong doc duoc anh: {image_path}")

    best_candidate, candidate_scores = select_best_candidate(detector, image)

    if save_preprocessed_dir:
        save_dir = Path(save_preprocessed_dir)
        save_dir.mkdir(parents=True, exist_ok=True)
        for view_name, view_image in build_preprocessed_views(image).items():
            cv2.imwrite(str(save_dir / f"{image_path.stem}_{view_name}.png"), view_image)

    ocr_lines: list[dict[str, Any]] = []

    for idx, line in enumerate(best_candidate.detector_result):
        box = line[0]
        crop = four_point_transform(best_candidate.image, box)
        if crop.size == 0:
            continue

        pil_img = Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))
        try:
            text = recognizer.predict(pil_img)
        except Exception as exc:  # pragma: no cover - runtime safeguard for OCR models
            text = f"ERROR: {exc}"

        ocr_lines.append(
            {
                "text": text,
                "box": box,
                "source_view": best_candidate.name,
            }
        )
        safe_log(f"[{best_candidate.name}:{idx}] {text}")

    if output_image_path:
        draw_debug_image(best_candidate.image, ocr_lines, output_image_path)

    latency_ms = (time.time() - started_at) * 1000.0

    return {
        "lines": ocr_lines,
        "meta": {
            "selected_view": best_candidate.name,
            "candidate_scores": candidate_scores,
            "detected_boxes": len(best_candidate.detector_result),
            "latency_ms": round(latency_ms, 2),
        },
    }
