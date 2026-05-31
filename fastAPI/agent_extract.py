from langchain.agents import create_agent
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from dotenv import load_dotenv
from run import OCR
from langchain_core.prompts import PromptTemplate
load_dotenv()
import os
import json
from langchain.messages import HumanMessage, AIMessage, SystemMessage
import re
from pprint import pprint

def convertSTR(content):
    match = re.search(
    r"```json\s*(.*?)\s*```",
    content,
    re.DOTALL)
    if match:
        data = json.loads(match.group(1))
    return data

def handleIMG(path):
    result = OCR(path)
    return result

class BaseInp(BaseModel):
    name_file: str
@tool(args_schema=BaseInp)
def toolReadFile(name_file: str):
    """Tool dùng để đọc quy tắc trả về"""
    with open(name_file, 'r', encoding="utf-8") as fo:
        data = json.load(fo)

    return {
        "message": data
    }

model = ChatOpenAI(
    model = os.getenv("MODEL_CHAT"),
    base_url= os.getenv("BASE_URL")
)

rules= toolReadFile.invoke({"name_file": "rules_response.md"})
result_ocr = handleIMG("dataset/images/a_lot_of_noise/menu_02.png")

message = [
    SystemMessage(content="Bạn là trợ lý AI giúp lấy ra các món ăn từ tọa độ và chuyển nó sang tiếng việt"),
    HumanMessage(content=f"""
    Bạn hãy chuyển đổi đầy đủ kết quả từ {result_ocr} sang {rules} JSON giúp tôi, chú ý tọa độ
""")
]

final = model.invoke(message)
content = final.content
# print(content)
data = convertSTR(content)
pprint(data)



