from __future__ import annotations

import re
import unicodedata
from typing import Any


PRICE_RE = re.compile(r"(\d[\d\.,]*)\s*([kK])?")
MULTISPACE_RE = re.compile(r"\s+")


def strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip().lower()
    text = strip_accents(text)
    text = text.replace("đ", "d")
    text = MULTISPACE_RE.sub(" ", text)
    return text


def slugify_name(value: Any) -> str:
    text = normalize_text(value)
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    text = MULTISPACE_RE.sub(" ", text).strip()
    return text


def normalize_price(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(round(value))

    text = normalize_text(value)
    match = PRICE_RE.search(text)
    if not match:
        digits = re.sub(r"[^\d]", "", text)
        return int(digits) if digits else None

    number, suffix = match.groups()
    digits = re.sub(r"[^\d]", "", number)
    if not digits:
        return None
    price = int(digits)
    if suffix:
        price *= 1000
    return price


def fuzzy_name_match(left: Any, right: Any, threshold: float = 0.88) -> bool:
    from difflib import SequenceMatcher

    left_norm = slugify_name(left)
    right_norm = slugify_name(right)
    if not left_norm or not right_norm:
        return False
    if left_norm == right_norm:
        return True
    return SequenceMatcher(a=left_norm, b=right_norm).ratio() >= threshold

