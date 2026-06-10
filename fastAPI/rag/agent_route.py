import ast
import json
import os
import re

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.messages import HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

load_dotenv()

rules = {
    "classifi": "RAG/OCR"
}


class BaseInp(BaseModel):
    exp: str = Field(description="Câu đầu vào của người dùng")


@tool(args_schema=BaseInp)
def toolCheckInp(exp: str):
    """Tool phân loại đầu vào"""
    llm = ChatOpenAI(
        model=os.getenv("MODEL_CHAT") or "gpt-4o-mini",
        base_url=os.getenv("BASE_URL"),
    )
    messages = [
        (
            "system",
            f"""Bạn là trợ lý AI, chuyên phân loại câu hỏi của người dùng.
            QUY TẮC:
            - Nếu người dùng hỏi những câu liên quan đến hệ thống thì trả về "RAG", hỏi về muốn trích xuất thông tin từ ảnh hoặc ocr hoặc gửi ảnh lên thì "OCR"
            - Phải trả về dạng JSON theo {rules}
            """,
        ),
        ("human", exp),
    ]
    return llm.invoke(messages)


def convertSTR(text):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None

    content = match.group()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return ast.literal_eval(content)


def _extract_route_text(q):
    if isinstance(q, dict):
        text_value = (q.get("text") or q.get("prompt") or "").strip()
        if text_value:
            return text_value
        if q.get("img_path") or q.get("image_base64"):
            return None
        return ""
    return q


def _heuristic_route(route_text):
    normalized = (route_text or "").strip().lower()
    if not normalized:
        return {"classifi": "RAG"}

    ocr_keywords = (
        "ocr",
        "trich xuat",
        "trích xuất",
        "doc anh",
        "đọc ảnh",
        "doc menu",
        "đọc menu",
        "anh menu",
        "ảnh menu",
        "base64",
        "hinh anh",
        "hình ảnh",
        "image",
        "img",
    )
    if any(keyword in normalized for keyword in ocr_keywords):
        return {"classifi": "OCR"}

    return {"classifi": "RAG"}


def agent_routes(q):
    route_text = _extract_route_text(q)
    if route_text is None:
        return {"classifi": "OCR"}

    llm = ChatOpenAI(
        model=os.getenv("MODEL_CHAT") or "gpt-4o-mini",
        base_url=os.getenv("BASE_URL"),
    )
    prompt = """
    Bạn là trợ lý AI, có nhiệm vụ chính là đưa ra kết luận là "RAG" hoặc "OCR"
    QUY TẮC:
    - BẮT BUỘC TRẢ VỀ JSON DỰA VÀO TOOL
    """
    agent = create_agent(llm, [toolCheckInp], system_prompt=prompt)

    rs = agent.invoke({"messages": [HumanMessage(content=route_text)]})["messages"][-1].content
    rs = convertSTR(rs)
    if isinstance(rs, dict) and rs.get("classifi") in {"RAG", "OCR"}:
        return rs
    return _heuristic_route(route_text)


if __name__ == "__main__":
    q = "Tôi có cái ảnh này cần nhờ bạn giúp đỡ trích xuất"
    rs = agent_routes(q)
    print(rs)
    print(type(rs))
