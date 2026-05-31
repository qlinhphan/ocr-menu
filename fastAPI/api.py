import json
import os
import re
import tempfile
from pathlib import Path
import cv2 as cv
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from langchain.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
import uvicorn

try:
    from .run import OCR
except ImportError:
    from run import OCR


load_dotenv()

app = FastAPI(title="Menu OCR API", version="1.0.0")

BASE_DIR = Path(__file__).resolve().parent
RULES_FILE = BASE_DIR / "rules_response.md"


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


def extract_menu_from_image(image_path: str):
    rules = load_rules()
    ocr_result = OCR(image_path)
    model = build_model()

    messages = [
        SystemMessage(
            content="Ban la tro ly AI giup lay ra cac mon an tu toa do va chuyen no sang tieng Viet."
        ),
        HumanMessage(
            content=(
                "Hay chuyen doi day du ket qua OCR sau thanh JSON theo dung cau truc mau.\n\n"
                f"Ket qua OCR:\n{ocr_result}\n\n"
                f"JSON mau/cau truc can tra ve:\n{rules}\n\n"
                "Hay uu tien dung toa do de ghep ten mon, mo ta va gia tien cho chinh xac. "
                "Chi tra ve duy nhat JSON hop le dung schema mau, khong them bat ky truong nao khac."
            )
        ),
    ]

    response = model.invoke(messages)
    parsed_data = convert_response_to_json(response.content)

    return parsed_data


@app.get("/")
def health_check():
    return {"message": "Menu OCR API is running"}


@app.post("/extract-menu")
async def extract_menu(file: UploadFile = File(...)):
    suffix = Path(file.filename or "menu_image").suffix or ".jpg"

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(await file.read())
            temp_path = temp_file.name

        result = await run_in_threadpool(extract_menu_from_image, temp_path)
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
