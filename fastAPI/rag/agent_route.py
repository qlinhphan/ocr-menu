
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
from langchain.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()
config = {"configurable": {"thread_id": 'user-123'}}


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


def _extract_route_text(q):
    if isinstance(q, dict):
        if q.get("img_path") or q.get("image_base64"):
            return None
        return q.get("text") or q.get("prompt") or ""
    return q


def agent_routes(q):
    route_text = _extract_route_text(q)
    if route_text is None:
        return {"classifi": "OCR"}

    llm = ChatOpenAI(model = os.getenv("MODEL_CHAT"), base_url=os.getenv("BASE_URL"))
    prompt = f"""
    Bạn là trợ AI, có nhiệm vụ chính là đưa ra kết luận là "RAG" hoặc "OCR"
    QUY TẮC:
    - BẮT BUỘC TRẢ VỀ JSON DỰA VÀO TOOL
"""
    agent = create_agent(llm, [toolCheckInp], system_prompt=prompt, checkpointer=memory)
    
    rs = agent.invoke({'messages': [HumanMessage(content=route_text)]}, config=config)['messages'][-1].content
    rs = convertSTR(rs)
    return rs

if __name__ == "__main__":
    q = "Tôi có cái ảnh này cần nhờ bạn giúp đỡ trích xuất"
    rs = agent_routes(q)
    print(rs)
    print(type(rs))
