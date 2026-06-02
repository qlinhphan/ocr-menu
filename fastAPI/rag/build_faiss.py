import numpy as np
import faiss
from connect_mg import connect_mg
from dotenv import load_dotenv
load_dotenv()
import os

mg = connect_mg(os.getenv("MONGODB_URI"))

dimension = 512

data = list(mg.find())

emb = np.array([d['embedding'] for d in data]).astype('float32')
faiss.normalize_L2(emb)
index = faiss.IndexFlatL2(dimension)
index.add(emb)

faiss.write_index(index, "faiss.index")
print('built faiss index successfully!')


