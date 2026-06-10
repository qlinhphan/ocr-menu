import json
import os
import shutil
import tempfile
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
import uvicorn

try:
    from .main import app as graph_app
except ImportError:
    from main import app as graph_app


app = FastAPI(title="RAG OCR Flow API", version="1.0.0")
FRONT_PUBLIC_DIR = Path(__file__).resolve().parents[2] / "front" / "public"


def _invoke_graph(inp):
    result = graph_app.invoke({"inp": inp})
    has_image_input = isinstance(inp, dict) and bool(inp.get("img_path") or inp.get("image_base64"))

    if "ocr_rs" in result:
        response = {
            "type": "OCR",
            "result": result["ocr_rs"],
            "flow": result,
        }
        if has_image_input:
            response["add"] = "Bạn có muốn lưu menu này không?"
        return response

    if "rag_rs" in result:
        return {
            "type": "RAG",
            "result": result["rag_rs"],
            "flow": result,
        }

    return {
        "type": "UNKNOWN",
        "result": result,
        "flow": result,
    }


def _copy_public_image(temp_path: str, suffix: str) -> str:
    public_image_name = f"{uuid.uuid4().hex}{suffix}"
    public_image_path = FRONT_PUBLIC_DIR / public_image_name
    public_image_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(temp_path, public_image_path)
    return f"/{public_image_name}"


@app.get("/")
def health_check():
    return {"message": "RAG OCR flow API is running"}


@app.post("/invoke")
async def invoke_flow(
    text: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
):
    if not text and not file:
        raise HTTPException(status_code=400, detail="Can gui it nhat mot trong 2 truong: text hoac file")

    temp_path = None
    public_path = None

    try:
        if file is not None:
            suffix = Path(file.filename or "menu_image").suffix or ".jpg"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                temp_file.write(await file.read())
                temp_path = temp_file.name

            payload = {
                "text": text or "Trich xuat noi dung tu anh menu nay",
                "img_path": temp_path,
            }
            result = await run_in_threadpool(_invoke_graph, payload)
            if result.get("type") == "OCR" and temp_path:
                public_path = _copy_public_image(temp_path, suffix)
                result["path_img"] = public_path
            return result

        return await run_in_threadpool(_invoke_graph, text)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=502, detail=f"Model tra ve JSON khong hop le: {exc}") from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Loi xu ly request: {exc}") from exc
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


def main():
    uvicorn.run("api:app", host="localhost", port=8001, reload=False)


if __name__ == "__main__":
    main()
