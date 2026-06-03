import json
import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
import uvicorn

try:
    from .main import app as graph_app
except ImportError:
    from main import app as graph_app


app = FastAPI(title="RAG OCR Flow API", version="1.0.0")


def _invoke_graph(inp):
    result = graph_app.invoke({"inp": inp})

    if "ocr_rs" in result:
        return {
            "type": "OCR",
            "result": result["ocr_rs"],
            "flow": result,
        }

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
            return await run_in_threadpool(_invoke_graph, payload)

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
    uvicorn.run("api:app", host="0.0.0.0", port=8001, reload=False)


if __name__ == "__main__":
    main()
