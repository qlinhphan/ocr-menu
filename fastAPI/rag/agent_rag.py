import os
import re

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

try:
    from .rag import searchRAG
except ImportError:
    from rag import searchRAG

load_dotenv()


def _build_model() -> ChatOpenAI:
    return ChatOpenAI(
        model=os.getenv("MODEL_CHAT") or "gpt-4o-mini",
        base_url=os.getenv("BASE_URL"),
    )


def _format_context(chunks: list[str]) -> str:
    return "\n\n".join(f"[Ngữ cảnh {idx}] {chunk}" for idx, chunk in enumerate(chunks, start=1))


def _rule_based_answer(contexts: list[str]) -> str:
    text = " ".join(contexts)
    markers = [
        r"(?:được\s+)?(?:làm|xây dựng|tạo ra|phát triển)\s+bởi\s+",
        r"bởi\s+",
    ]
    for marker in markers:
        match = re.search(marker, text, re.IGNORECASE)
        if match:
            tail = text[match.end():]
            name_match = re.match(r"([A-ZĐ][\wÀ-ỹ]+(?:\s+[A-ZĐ][\wÀ-ỹ]+){1,5})", tail)
            if name_match:
                author = name_match.group(1).strip().rstrip(".")
                return f"Hệ thống này được làm bởi {author}."
    return "TÔI KHÔNG BIẾT!"


def agent_rags(q: str) -> str:
    contexts = searchRAG(q)
    if not contexts:
        return "TÔI KHÔNG BIẾT!"

    model = _build_model()
    messages = [
        SystemMessage(
            content=(
                "Bạn là trợ lý AI trả lời câu hỏi về hệ thống OCR menu này. "
                "Chỉ được dùng thông tin trong phần ngữ cảnh. "
                "Nếu ngữ cảnh không đủ để kết luận thì trả về đúng chuỗi 'TÔI KHÔNG BIẾT!'. "
                "Nếu có đủ thông tin thì trả lời ngắn gọn, trực tiếp và bằng tiếng Việt."
            )
        ),
        HumanMessage(
            content=(
                f"Câu hỏi: {q}\n\n"
                f"Ngữ cảnh:\n{_format_context(contexts)}"
            )
        ),
    ]
    try:
        response = model.invoke(messages)
        return (response.content or "").strip() or _rule_based_answer(contexts)
    except Exception:
        return _rule_based_answer(contexts)


if __name__ == "__main__":
    while True:
        q = input("Bạn: ")
        if q == "bye":
            print("AI: bye!!")
            break
        print("AI: ", agent_rags(q))
