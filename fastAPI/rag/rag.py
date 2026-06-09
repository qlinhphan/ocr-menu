from pathlib import Path
import os

import faiss
import numpy as np
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

try:
    from .connect_mg import connect_mg
except ImportError:
    from connect_mg import connect_mg

load_dotenv()

mg = connect_mg(os.getenv("MONGODB_URI"))
BASE_DIR = Path(__file__).resolve().parent
FAISS_INDEX_PATH = BASE_DIR / "faiss.index"


def searchRAG(query: str) -> str:
    emb = OpenAIEmbeddings(model="text-embedding-3-large", base_url=os.getenv("BASE_URL"), dimensions=512)
    query_emb = np.array([emb.embed_query(query)]).astype('float32')
    faiss.normalize_L2(query_emb)
    index = faiss.read_index(str(FAISS_INDEX_PATH))
    d, i = index.search(query_emb, k=10)
    i_need = i[0].tolist()
    data_list = list(mg.find())
    data = [data_list[i]['text'] for i in i_need]
    return data

if __name__ == "__main__":
    query = "Ai tạo ra sản phẩm này?"
    result = searchRAG(query)
    print(result)
