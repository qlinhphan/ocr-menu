from functools import lru_cache
from pathlib import Path
import os
import re
import unicodedata

import faiss
import numpy as np
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

try:
    from .connect_mg import connect_mg
except ImportError:
    from connect_mg import connect_mg

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
FAISS_INDEX_PATH = BASE_DIR / "faiss.index"
DOCS_PATH = BASE_DIR / "docs.txt"


def _build_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model="text-embedding-3-large",
        base_url=os.getenv("BASE_URL"),
        dimensions=512,
    )


@lru_cache(maxsize=1)
def _load_index():
    return faiss.read_index(str(FAISS_INDEX_PATH))


@lru_cache(maxsize=1)
def _split_docs_file() -> list[str]:
    if not DOCS_PATH.exists():
        return []

    text = DOCS_PATH.read_text(encoding="utf-8").strip()
    if not text:
        return []

    splitter = RecursiveCharacterTextSplitter(chunk_size=120, chunk_overlap=30)
    return [chunk for chunk in splitter.split_text(text) if chunk.strip()]


@lru_cache(maxsize=1)
def _load_mongo_chunks() -> list[str]:
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        return []

    collection = connect_mg(mongodb_uri)
    docs = list(collection.find().sort("_id", 1))
    return [doc.get("text", "").strip() for doc in docs if doc.get("text")]


def _load_corpus() -> list[str]:
    index = _load_index()

    docs_chunks = _split_docs_file()
    if len(docs_chunks) == index.ntotal:
        return docs_chunks

    mongo_chunks = _load_mongo_chunks()
    if len(mongo_chunks) == index.ntotal:
        return mongo_chunks

    return docs_chunks or mongo_chunks


def _normalize_text(text: str) -> list[str]:
    folded = _ascii_fold(text)
    return [token for token in re.findall(r"[a-z0-9_]+", folded) if len(token) > 1]


def _ascii_fold(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(char for char in normalized if not unicodedata.combining(char)).lower()


def _is_creator_query(query: str) -> bool:
    normalized = _ascii_fold(query)
    asks_who = bool(re.search(r"\bai\b", normalized))
    asks_creator = any(keyword in normalized for keyword in ("tao", "lam", "xay dung", "phat trien"))
    return asks_who and asks_creator


def _lexical_rank(query: str, corpus: list[str], k: int) -> list[str]:
    query_tokens = set(_normalize_text(query))
    creator_query = _is_creator_query(query)
    scored = []
    for idx, chunk in enumerate(corpus):
        chunk_tokens = set(_normalize_text(chunk))
        score = len(query_tokens & chunk_tokens)
        folded_chunk = _ascii_fold(chunk)
        if creator_query and any(marker in folded_chunk for marker in ("lam boi", "xay dung boi", "phat trien boi", "duoc lam boi")):
            score += 10
        if score:
            scored.append((score, idx, chunk))

    scored.sort(key=lambda item: (-item[0], item[1]))
    return [chunk for _, _, chunk in scored[:k]]


def searchRAG(query: str, k: int = 4) -> list[str]:
    normalized_query = (query or "").strip()
    if not normalized_query:
        return []

    corpus = _load_corpus()
    if not corpus:
        return []

    index = _load_index()
    top_k = min(max(k, 1), len(corpus))

    try:
        embeddings = _build_embeddings()
        query_emb = np.array([embeddings.embed_query(normalized_query)], dtype="float32")
        faiss.normalize_L2(query_emb)
        _, indices = index.search(query_emb, k=top_k)

        results = []
        seen = set()
        for idx in indices[0].tolist():
            if idx < 0 or idx >= len(corpus):
                continue
            chunk = corpus[idx].strip()
            if not chunk or chunk in seen:
                continue
            seen.add(chunk)
            results.append(chunk)

        if results:
            return results
    except Exception:
        pass

    return _lexical_rank(normalized_query, corpus, top_k)


if __name__ == "__main__":
    query = "Ai tạo ra sản phẩm này?"
    result = searchRAG(query)
    print(result)
