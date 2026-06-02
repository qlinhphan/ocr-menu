from langchain.agents import create_agent
from dotenv import load_dotenv
load_dotenv()
import os
from connect_mg import connect_mg
from langchain_core.tools import tool
from pydantic import BaseModel

class BaseInput(BaseModel):
    query: str
@tool(args_schema=BaseInput)
def searchRAG(query: str) -> str:
    

mg = connect_mg(os.getenv("MONGODB_URI"))
