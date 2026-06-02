import pymongo
from dotenv import load_dotenv
load_dotenv()
import os

def connect_mg(address):
    myclient = pymongo.MongoClient(address)
    mydb = myclient["ocr"]
    mycol = mydb["rag"]
    return mycol

if __name__ == "__main__":
    address = os.getenv("MONGODB_URI")
    mycol = connect_mg(address)
    mycol.insert_one({"name": "test", "value": 123})