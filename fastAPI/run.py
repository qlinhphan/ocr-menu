from paddleocr import PaddleOCR
from vietocr.tool.predictor import Predictor
from vietocr.tool.config import Cfg

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
import sys


def safe_log(message):
    try:
        print(message)
    except UnicodeEncodeError:
        fallback = message.encode("utf-8", errors="replace").decode("utf-8")
        try:
            sys.stdout.buffer.write((fallback + "\n").encode("utf-8", errors="replace"))
        except Exception:
            print(fallback.encode(sys.stdout.encoding or "ascii", errors="replace").decode(sys.stdout.encoding or "ascii"))


def load_unicode_font(size=20):
    font_candidates = [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/tahoma.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
    ]

    for font_path in font_candidates:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size=size)
            except OSError:
                continue

    return ImageFont.load_default()


# =========================
# Perspective Transform
# =========================
def four_point_transform(image, box):

    pts = np.array(box, dtype=np.float32)

    # PaddleOCR trả về:
    # [top-left, top-right, bottom-right, bottom-left]
    tl, tr, br, bl = pts

    widthA = np.linalg.norm(br - bl)
    widthB = np.linalg.norm(tr - tl)

    maxWidth = max(int(widthA), int(widthB))

    heightA = np.linalg.norm(tr - br)
    heightB = np.linalg.norm(tl - bl)

    maxHeight = max(int(heightA), int(heightB))

    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]
    ], dtype=np.float32)

    M = cv2.getPerspectiveTransform(pts, dst)

    warped = cv2.warpPerspective(
        image,
        M,
        (maxWidth, maxHeight)
    )

    return warped


# =========================
# OCR
# =========================
def OCR(img_path, output_image_path=None):

    detector = PaddleOCR(
        use_angle_cls=True,
        lang="vi"
    )

    config = Cfg.load_config_from_name("vgg_transformer")

    config["device"] = "cpu"

    recognizer = Predictor(config)

    result = detector.ocr(img_path)

    img = cv2.imread(img_path)
    cv2.imwrite("start.jpg", img)

    draw_img = img.copy()
    rgb_draw_img = cv2.cvtColor(draw_img, cv2.COLOR_BGR2RGB)
    pil_draw_img = Image.fromarray(rgb_draw_img)
    text_draw = ImageDraw.Draw(pil_draw_img)
    debug_font = load_unicode_font(size=20)

    final_result = []

    os.makedirs("debug_crop", exist_ok=True)

    for idx, line in enumerate(result[0]):

        box = line[0]

        # ----------------------
        # Crop bằng Perspective
        # ----------------------
        crop = four_point_transform(img, box)

        if crop.size == 0:
            continue

        # lưu crop để debug
        cv2.imwrite(
            f"debug_crop/crop_{idx}.jpg",
            crop
        )

        # ----------------------
        # OpenCV -> PIL
        # ----------------------
        pil_img = Image.fromarray(
            cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
        )

        # ----------------------
        # VietOCR
        # ----------------------
        try:
            text = recognizer.predict(pil_img)
        except Exception as e:
            text = f"ERROR: {e}"

        final_result.append({
            "text": text,
            "box": box
        })

        # ----------------------
        # Draw Polygon
        # ----------------------
        pts = np.array(box, dtype=np.int32)

        cv2.polylines(
            draw_img,
            [pts],
            True,
            (0, 255, 0),
            2
        )

        text_draw.line(
            [tuple(point) for point in pts] + [tuple(pts[0])],
            fill=(0, 255, 0),
            width=2
        )

        x = int(box[0][0])
        y = int(box[0][1])

        text_draw.text(
            (x, max(0, y - 24)),
            text,
            font=debug_font,
            fill=(255, 0, 0)
        )

        safe_log(f"[{idx}] {text}")

    draw_img = cv2.cvtColor(np.array(pil_draw_img), cv2.COLOR_RGB2BGR)

    if output_image_path:
        output_dir = os.path.dirname(output_image_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        cv2.imwrite(output_image_path, draw_img)

    # safe_log("\nSaved: output_vietocr.jpg")

    return final_result


if __name__ == "__main__":

    result = OCR(
        "dataset/images/beautiful_photos/menu_08.png"
    )

    from pprint import pprint
    pprint(result)
