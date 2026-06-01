import json
import os
import re
import tempfile
import uuid
from pathlib import Path
import cv2 as cv
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from langchain.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
import uvicorn

try:
    from .run import OCR
except ImportError:
    from run import OCR


load_dotenv()

app = FastAPI(title="Menu OCR API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
RULES_FILE = BASE_DIR / "rules_response.md"
FRONT_PUBLIC_DIR = BASE_DIR.parent / "front" / "public"


def load_rules() -> str:
    if not RULES_FILE.exists():
        raise FileNotFoundError(f"Khong tim thay file rules: {RULES_FILE}")

    with RULES_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return json.dumps(data, ensure_ascii=False, indent=2)


def convert_response_to_json(content: str):
    fenced_match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)
    raw_json = fenced_match.group(1) if fenced_match else content.strip()
    return json.loads(raw_json)


def build_model() -> ChatOpenAI:
    model_name = os.getenv("MODEL_CHAT")
    base_url = os.getenv("BASE_URL")

    if not model_name:
        raise RuntimeError("Thieu bien moi truong MODEL_CHAT")

    return ChatOpenAI(model=model_name, base_url=base_url)


def extract_menu_from_image(image_path: str, output_image_path: str, public_image_path: str):
    rules = load_rules()
    ocr_result = OCR(image_path, output_image_path=output_image_path)
    model = build_model()

    messages = [
        SystemMessage(
            content=(
                "Ban la tro ly AI chuyen ket qua OCR menu thanh JSON co cau truc chinh xac. "
                "Ban phai nhan dien va tach dung cac the loai mon trong menu dua tren tieu de, "
                "bo cuc va toa do."
            )
        ),
        HumanMessage(
            content=(
                "Hay chuyen doi day du ket qua OCR sau thanh JSON theo dung cau truc mau.\n\n"
                f"Ket qua OCR:\n{ocr_result}\n\n"
                f"JSON mau/cau truc can tra ve:\n{rules}\n\n"
                "Quy tac bat buoc:\n"
                "- Truong categories la mot mang dong, co the co 1, 2, 3 hoac nhieu hon the loai.\n"
                "- Neu menu co nhieu nhom nhu do an, do uong, trang mieng, topping..., phai tach thanh nhieu category rieng biet.\n"
                "- Khong duoc gop tat ca mon vao mot category neu OCR cho thay co nhieu tieu de nhom khac nhau.\n"
                "- Ten category phai lay theo noi dung thuc te tren menu; chi dung ten chung nhu 'Do an' hoac 'Do uong' neu menu that su the hien nhu vay.\n"
                "- Uu tien dung toa do va vi tri de ghep ten mon, mo ta, gia tien va de xac dinh mon thuoc nhom nao.\n"
                "- Neu khong thay tieu de nhom ro rang, moi duoc gom cac mon lien quan vao cung mot category hop ly.\n"
                "- Chi tra ve duy nhat JSON hop le dung schema mau, khong them bat ky truong nao khac."
            )
        ),
    ]

    response = model.invoke(messages)
    parsed_data = convert_response_to_json(response.content)
    parsed_data["path_img"] = public_image_path

    return parsed_data


@app.get("/")
def health_check():
    return {"message": "Menu OCR API is running"}


@app.post("/extract-menu")
async def extract_menu(file: UploadFile = File(...)):
    suffix = Path(file.filename or "menu_image").suffix or ".jpg"

    try:
        image_name = f"{uuid.uuid4().hex}img.jpg"
        output_image_path = str(FRONT_PUBLIC_DIR / image_name)
        public_image_path = f"/{image_name}"

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(await file.read())
            temp_path = temp_file.name

        result = await run_in_threadpool(
            extract_menu_from_image,
            temp_path,
            output_image_path,
            public_image_path,
        )
        return result
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Model tra ve noi dung khong phai JSON hop le: {exc}",
        ) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Loi xu ly anh: {exc}") from exc
    finally:
        if "temp_path" in locals():
            try:
                os.remove(temp_path)
            except OSError:
                pass


def main():
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()
