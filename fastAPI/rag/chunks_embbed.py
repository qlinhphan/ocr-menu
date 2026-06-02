from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from matplotlib import text
from openai import embeddings
from dotenv import load_dotenv
load_dotenv()
import os
from connect_mg import connect_mg

mg = connect_mg(os.getenv("MONGODB_URI"))

def chunks_embbed(text):
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large", base_url=os.getenv("BASE_URL"), dimensions=512)
    # text = "This is a blog post on vector embeddings."
    embeddings_result = embeddings.embed_query(text)
    return embeddings_result


# 1. Initialize the text loader with your file path
loader = TextLoader("docs.txt", encoding="utf-8")

# 2. Extract data into LangChain Document objects
documents = loader.load()
# print(documents[0].page_content)

text_splitter = RecursiveCharacterTextSplitter(chunk_size=120, chunk_overlap=30)
documents = text_splitter.split_documents(documents)

# print(documents)

docs_to_insert = [{
    "text": doc.page_content,
    "embedding": chunks_embbed(doc.page_content)
} for doc in documents]

print(docs_to_insert)

print(len(docs_to_insert))

result = mg.insert_many(docs_to_insert)

print("save successfully!")


