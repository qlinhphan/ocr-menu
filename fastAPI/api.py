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
                "Bạn là trợ lý AI chuyên chuyển kết quả OCR menu thành JSON có cấu trúc chính xác. "
                "Nhiệm vụ quan trọng nhất là gán món vào đúng category theo tiêu đề nhóm, bố cục, "
                "tọa độ, cột và khối hiển thị trên menu. "
                "Bạn phải ưu tiên bằng chứng thị giác từ OCR/layout hơn suy luận ngữ nghĩa của tên món."
            )
        ),
        HumanMessage(
            content=(
                "Hãy chuyển đổi đầy đủ kết quả OCR sau thành JSON đúng cấu trúc mẫu.\n\n"
                f"Kết quả OCR:\n{ocr_result}\n\n"
                f"JSON mẫu/cấu trúc cần trả về:\n{rules}\n\n"
                "Quy tắc bắt buộc khi phân nhóm category:\n"
                "- categories là mảng động, có thể có 1 hoặc nhiều category.\n"
                "- Nếu menu có nhiều tiêu đề nhóm khác nhau thì phải tách đúng theo từng nhóm hiển thị trên menu.\n"
                "- Không được gộp tất cả món vào một category nếu OCR cho thấy nhiều tiêu đề nhóm riêng.\n"
                "- Tên category phải lấy từ chính tiêu đề xuất hiện trên menu; chỉ dùng tên chung như 'Đồ uống' nếu menu thật sự chỉ có một nhóm chung như vậy.\n"
                "- Phải ưu tiên tiêu đề, dòng ngăn cách, cột, khối, tọa độ và vị trí gần nhất để quyết định món thuộc category nào.\n"
                "- Mỗi món phải được gán vào category gần nhất về mặt bố cục, không gán theo cảm tính.\n"
                "- Không được suy diễn kiểu: thấy tên món giống trà sữa thì tự chuyển sang nhóm 'TRÀ SỮA', thấy tên giống nước ép thì tự chuyển sang 'NƯỚC ÉP', nếu vị trí OCR của món đó đang nằm dưới tiêu đề khác.\n"
                "- Nếu một món nằm dưới header 'CAFE' thì giữ nó trong 'CAFE' dù tên món có thể nhìn giống trà hoặc nước trái cây, trừ khi OCR/toạ độ cho thấy rõ nó thuộc một nhóm khác.\n"
                "- Nếu một món nằm dưới header 'TRÀ SỮA' thì giữ nó trong 'TRÀ SỮA' ngay cả khi tên món không chứa chữ 'trà sữa'.\n"
                "- Nếu một món nằm dưới header 'NƯỚC ÉP' thì chỉ xếp vào đó khi vị trí của nó thực sự thuộc khối 'NƯỚC ÉP'.\n"
                "- Nếu không nhìn thấy tiêu đề nhóm rõ ràng, hãy gom theo từng cụm món gần nhau trong cùng cột/cùng block; chỉ khi đó mới suy luận category hợp lý.\n"
                "- Phải giữ đúng thứ tự category từ trên xuống dưới hoặc từ trái sang phải theo bố cục menu.\n"
                "- Trong mỗi category, giữ đúng thứ tự món theo vị trí xuất hiện trên menu.\n"
                "- Không tạo category mới chỉ vì bạn hiểu ý nghĩa tên món; chỉ tạo category khi có bằng chứng từ OCR/layout.\n"
                "- Không sửa tên category thành tên 'đẹp hơn'; giữ nguyên hoặc chuẩn hóa nhẹ lỗi OCR nhưng vẫn phải bám sát chữ gốc trên menu.\n"
                "- Nếu phân vân giữa 2 category, chọn category có bằng chứng vị trí mạnh hơn thay vì chọn theo ngữ nghĩa tên món.\n"
                "- Chỉ trả về duy nhất JSON hợp lệ đúng schema mẫu, không giải thích, không thêm trường ngoài schema."
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
