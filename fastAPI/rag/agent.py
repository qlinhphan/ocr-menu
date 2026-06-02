from langchain.agents import create_agent
from dotenv import load_dotenv
load_dotenv()
from langchain_openai import OpenAIEmbeddings
import os
from langchain_openai import ChatOpenAI
from connect_mg import connect_mg
from langchain_core.tools import tool
from pydantic import BaseModel
from rag import searchRAG
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver
memory = MemorySaver()
config = {"configurable": {"thread_id": "user-123"}}
class BaseInput(BaseModel):
    query: str
@tool(args_schema=BaseInput)
def searchRAGTool(query: str) -> str:
    """Tool dùng để truy vấn dễ liệu"""
    print("<<<<< SEARCH RAG >>>>>")
    result = searchRAG(query)
    return result

llm = ChatOpenAI(model="gpt-4o-mini", base_url=os.getenv("BASE_URL"), temperature=0.1)

prompt = f"""
Bạn là một trợ lý ảo thông minh, có khả năng truy vấn dữ liệu từ một cơ sở dữ liệu lớn. Khi nhận được một câu hỏi, bạn PHẢI sử dụng công cụ searchRAGTool để tìm kiếm thông tin liên quan trong cơ sở dữ liệu và trả về kết quả cho người dùng. Hãy đảm bảo rằng bạn hiểu rõ câu hỏi và sử dụng công cụ một cách hiệu quả để cung cấp câu trả lời chính xác và hữu ích nhất có thể.
"""
agent = create_agent(llm, tools=[searchRAGTool], system_prompt=prompt, checkpointer=memory)

while True:
    q = input("Bạn: ")
    if q == "bye":
        print("AI: bye!!")
        break
    rs = agent.invoke({"messages": [HumanMessage(content=q)]}, config=config)['messages'][-1].content
    print("AI: ", rs)




# mg = connect_mg(os.getenv("MONGODB_URI"))
