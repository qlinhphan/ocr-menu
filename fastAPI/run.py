from paddleocr import PaddleOCR
from vietocr.tool.predictor import Predictor
from vietocr.tool.config import Cfg

import cv2
import numpy as np
from PIL import Image
import os


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
def OCR(img_path):

    detector = PaddleOCR(
        use_angle_cls=True,
        lang="vi"
    )

    config = Cfg.load_config_from_name("vgg_transformer")

    config["device"] = "cpu"

    recognizer = Predictor(config)

    result = detector.ocr(img_path)

    img = cv2.imread(img_path)

    draw_img = img.copy()

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

        x = int(box[0][0])
        y = int(box[0][1])

        cv2.putText(
            draw_img,
            text,
            (x, max(20, y - 5)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 0, 255),
            1
        )

        print(f"[{idx}] {text}")

    cv2.imwrite(
        "output_vietocr.jpg",
        draw_img
    )

    print("\nSaved: output_vietocr.jpg")

    return final_result


if __name__ == "__main__":

    result = OCR(
        "dataset/images/beautiful_photos/menu_08.png"
    )

    from pprint import pprint
    pprint(result)