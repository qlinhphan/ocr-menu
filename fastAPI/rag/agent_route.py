
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from dotenv import load_dotenv
from langchain_core.tools import tool
load_dotenv()
import os
from pydantic import BaseModel, Field
import re
import json
import ast


rules = {
    "classifi": "RAG/OCR"
}

class BaseInp(BaseModel):
    exp: str = Field(description="Câu đầu vào của người dùng")
@tool(args_schema=BaseInp)
def toolCheckInp(exp: str):
    """Tool phân loại đầu vào"""
    llm = ChatOpenAI(model = os.getenv("MODEL_CHAT"), base_url=os.getenv("BASE_URL"))
    messages = [
        (
            "system",
            f"""Bạn là trợ lý AI, chuyên phân loại câu hỏi của người dùng.
            QUY TẮC:
            - Nếu người dùng hỏi những câu liên quan đến hệ thống thì trả về "RAG", hỏi về muốn trích xuất thông tin từ ảnh hoặc ocr hoặc gửi ảnh lên thì "OCR"
            - Phải trả về dạng JSON theo {rules}
            """,
        ),
        ("human", exp)
    ]
    rs = llm.invoke(messages)
    return rs

def convertSTR(text):
    match = re.search(r'\{.*\}', text, re.DOTALL)

    if not match:
        return None

    content = match.group()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return ast.literal_eval(content)

def agent_routes(q):
    rs = toolCheckInp.invoke(q)
    # rs = convertSTR(rs.content)
    rs = rs.content
    rs = convertSTR(rs)
    return rs

