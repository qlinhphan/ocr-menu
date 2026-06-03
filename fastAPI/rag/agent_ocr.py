import base64
import json
import os
import re
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np
from dotenv import load_dotenv
from langchain.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from PIL import Image, ImageDraw, ImageFont
from paddleocr import PaddleOCR
from pydantic import BaseModel, Field, model_validator
from vietocr.tool.config import Cfg
from vietocr.tool.predictor import Predictor
from langchain.agents import create_agent

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
RULES_FILE = BASE_DIR / "rules_response.md"


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


def four_point_transform(image, box):
    pts = np.array(box, dtype=np.float32)

    # PaddleOCR tra ve:
    # [top-left, top-right, bottom-right, bottom-left]
    tl, tr, br, bl = pts

    widthA = np.linalg.norm(br - bl)
    widthB = np.linalg.norm(tr - tl)
    maxWidth = max(int(widthA), int(widthB))

    heightA = np.linalg.norm(tr - br)
    heightB = np.linalg.norm(tl - bl)
    maxHeight = max(int(heightA), int(heightB))

    dst = np.array(
        [
            [0, 0],
            [maxWidth - 1, 0],
            [maxWidth - 1, maxHeight - 1],
            [0, maxHeight - 1],
        ],
        dtype=np.float32,
    )

    transform_matrix = cv2.getPerspectiveTransform(pts, dst)
    warped = cv2.warpPerspective(image, transform_matrix, (maxWidth, maxHeight))
    return warped


def _resolve_image_path(img_path: str | None, image_base64: str | None) -> tuple[str, str | None]:
    if img_path:
        path = Path(img_path).expanduser()
        if not path.exists():
            raise FileNotFoundError(f"Khong tim thay anh: {path}")
        return str(path), None

    if not image_base64:
        raise ValueError("Can truyen img_path hoac image_base64")

    raw_base64 = image_base64
    if "," in image_base64 and image_base64.strip().lower().startswith("data:image"):
        raw_base64 = image_base64.split(",", 1)[1]

    try:
        image_bytes = base64.b64decode(raw_base64)
    except Exception as exc:
        raise ValueError("image_base64 khong hop le") from exc

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    try:
        temp_file.write(image_bytes)
        temp_file.flush()
    finally:
        temp_file.close()

    return temp_file.name, temp_file.name


def _run_ocr(img_path, output_image_path=None):
    detector = PaddleOCR(use_angle_cls=True, lang="vi")

    config = Cfg.load_config_from_name("vgg_transformer")
    config["device"] = "cpu"
    recognizer = Predictor(config)

    result = detector.ocr(img_path)

    img = cv2.imread(img_path)
    if img is None:
        raise ValueError(f"Khong doc duoc anh tu duong dan: {img_path}")

    draw_img = img.copy()
    rgb_draw_img = cv2.cvtColor(draw_img, cv2.COLOR_BGR2RGB)
    pil_draw_img = Image.fromarray(rgb_draw_img)
    text_draw = ImageDraw.Draw(pil_draw_img)
    debug_font = load_unicode_font(size=20)

    final_result = []
    os.makedirs("debug_crop", exist_ok=True)

    ocr_lines = result[0] if result else []

    for idx, line in enumerate(ocr_lines):
        box = line[0]
        crop = four_point_transform(img, box)

        if crop.size == 0:
            continue

        cv2.imwrite(f"debug_crop/crop_{idx}.jpg", crop)

        pil_img = Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))

        try:
            text = recognizer.predict(pil_img)
        except Exception as exc:
            text = f"ERROR: {exc}"

        final_result.append({"text": text, "box": box})

        pts = np.array(box, dtype=np.int32)
        cv2.polylines(draw_img, [pts], True, (0, 255, 0), 2)

        text_draw.line([tuple(point) for point in pts] + [tuple(pts[0])], fill=(0, 255, 0), width=2)

        x = int(box[0][0])
        y = int(box[0][1])
        text_draw.text((x, max(0, y - 24)), text, font=debug_font, fill=(255, 0, 0))

        safe_log(f"[{idx}] {text}")

    draw_img = cv2.cvtColor(np.array(pil_draw_img), cv2.COLOR_RGB2BGR)

    if output_image_path:
        output_dir = os.path.dirname(output_image_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        cv2.imwrite(output_image_path, draw_img)

    return final_result


def _load_rules() -> str:
    if not RULES_FILE.exists():
        raise FileNotFoundError(f"Khong tim thay file rules: {RULES_FILE}")

    with RULES_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return json.dumps(data, ensure_ascii=False, indent=2)


def _convert_response_to_json(content: str):
    fenced_match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)
    raw_json = fenced_match.group(1) if fenced_match else content.strip()
    return json.loads(raw_json)


def _build_model() -> ChatOpenAI:
    model_name = os.getenv("MODEL_CHAT")
    base_url = os.getenv("BASE_URL")

    if not model_name:
        raise RuntimeError("Thieu bien moi truong MODEL_CHAT")

    return ChatOpenAI(model=model_name, base_url=base_url)


def _structure_menu_with_llm(ocr_result):
    rules = _load_rules()
    model = _build_model()

    messages = [
        SystemMessage(
            content=(
                "Ban la tro ly AI chuyen chuyen ket qua OCR menu thanh JSON co cau truc chinh xac. "
                "Nhiem vu quan trong nhat la gan mon vao dung category theo tieu de nhom, bo cuc, "
                "toa do, cot va khoi hien thi tren menu. "
                "Ban phai uu tien bang chung thi giac tu OCR/layout hon suy luan ngu nghia cua ten mon."
            )
        ),
        HumanMessage(
            content=(
                "Hay chuyen doi day du ket qua OCR sau thanh JSON dung cau truc mau.\n\n"
                f"Ket qua OCR:\n{ocr_result}\n\n"
                f"JSON mau/cau truc can tra ve:\n{rules}\n\n"
                "Quy tac bat buoc khi phan nhom category:\n"
                "- categories la mang dong, co the co 1 hoac nhieu category.\n"
                "- Neu menu co nhieu tieu de nhom khac nhau thi phai tach dung theo tung nhom hien thi tren menu.\n"
                "- Khong duoc gop tat ca mon vao mot category neu OCR cho thay nhieu tieu de nhom rieng.\n"
                "- Ten category phai lay tu chinh tieu de xuat hien tren menu; chi dung ten chung nhu 'Do uong' neu menu that su chi co mot nhom chung nhu vay.\n"
                "- Phai uu tien tieu de, dong ngan cach, cot, khoi, toa do va vi tri gan nhat de quyet dinh mon thuoc category nao.\n"
                "- Moi mon phai duoc gan vao category gan nhat ve mat bo cuc, khong gan theo cam tinh.\n"
                "- Khong duoc suy dien kieu: thay ten mon giong tra sua thi tu chuyen sang nhom 'TRA SUA', thay ten giong nuoc ep thi tu chuyen sang 'NUOC EP', neu vi tri OCR cua mon do dang nam duoi tieu de khac.\n"
                "- Neu mot mon nam duoi header 'CAFE' thi giu no trong 'CAFE' du ten mon co the nhin giong tra hoac nuoc trai cay, tru khi OCR/toa do cho thay ro no thuoc mot nhom khac.\n"
                "- Neu mot mon nam duoi header 'TRA SUA' thi giu no trong 'TRA SUA' ngay ca khi ten mon khong chua chu 'tra sua'.\n"
                "- Neu mot mon nam duoi header 'NUOC EP' thi chi xep vao do khi vi tri cua no thuc su thuoc khoi 'NUOC EP'.\n"
                "- Neu khong nhin thay tieu de nhom ro rang, hay gom theo tung cum mon gan nhau trong cung cot/cung block; chi khi do moi suy luan category hop ly.\n"
                "- Phai giu dung thu tu category tu tren xuong duoi hoac tu trai sang phai theo bo cuc menu.\n"
                "- Trong moi category, giu dung thu tu mon theo vi tri xuat hien tren menu.\n"
                "- Khong tao category moi chi vi ban hieu y nghia ten mon; chi tao category khi co bang chung tu OCR/layout.\n"
                "- Khong sua ten category thanh ten 'dep hon'; giu nguyen hoac chuan hoa nhe loi OCR nhung van phai bam sat chu goc tren menu.\n"
                "- Neu phan van giua 2 category, chon category co bang chung vi tri manh hon thay vi chon theo ngu nghia ten mon.\n"
                "- Chi tra ve duy nhat JSON hop le dung schema mau, khong giai thich, khong them truong ngoai schema."
            )
        ),
    ]

    response = model.invoke(messages)
    return _convert_response_to_json(response.content)


class OCRToolInput(BaseModel):
    img_path: str | None = Field(default=None, description="Duong dan local toi file anh menu")
    image_base64: str | None = Field(
        default=None,
        description="Anh menu dang base64. Co the la raw base64 hoac data URL data:image/...;base64,...",
    )
    output_image_path: str | None = Field(
        default=None,
        description="Neu muon luu anh debug da ve box OCR thi truyen duong dan output",
    )
    include_raw_ocr: bool = Field(
        default=False,
        description="Neu = true thi tra kem ket qua OCR tho trong truong raw_ocr",
    )

    @model_validator(mode="after")
    def validate_source(self):
        if not self.img_path and not self.image_base64:
            raise ValueError("Phai cung cap img_path hoac image_base64")
        return self


@tool(args_schema=OCRToolInput)
def OCRTool(
    img_path: str | None = None,
    image_base64: str | None = None,
    output_image_path: str | None = None,
    include_raw_ocr: bool = False,
):
    """Doc OCR tu anh menu, sau do dung LLM ep output thanh JSON giong fastAPI/api.py."""
    print("<<<<< TOOL OCR >>>>>")
    resolved_path = None
    temp_path = None

    try:
        resolved_path, temp_path = _resolve_image_path(img_path=img_path, image_base64=image_base64)
        ocr_result = _run_ocr(resolved_path, output_image_path=output_image_path)
        structured_result = _structure_menu_with_llm(ocr_result)
        if include_raw_ocr:
            structured_result["raw_ocr"] = ocr_result
        return structured_result
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass

# llm = ChatOpenAI(model = os.getenv("MODEL_CHAT"), base_url=os.getenv("BASE_URL"))

# agent = 


if __name__ == "__main__":
    path_img = "D:/ttsVin/DVX-OCR/fastAPI/dataset/images/a_lot_of_noise/menu_01.png"
    result = OCRTool.invoke({"img_path": path_img})
