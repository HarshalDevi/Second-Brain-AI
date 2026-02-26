import re
from dataclasses import dataclass


@dataclass
class Chunk:
    index: int
    text: str
    token_count: int | None = None


def normalize_text(text: str) -> str:
    t = text.replace("\x00", " ")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def chunk_text(text: str, max_chars: int = 1200, overlap: int = 150) -> list[Chunk]:
    """
    Simple deterministic chunker:
    - Works well for take-home
    - Keeps overlaps for context continuity
    """
    text = normalize_text(text)
    if not text:
        return []

    chunks: list[Chunk] = []
    i = 0
    idx = 0
    n = len(text)

    while i < n:
        end = min(i + max_chars, n)
        chunk = text[i:end].strip()
        if chunk:
            chunks.append(Chunk(index=idx, text=chunk))
            idx += 1
        if end == n:
            break
        i = max(0, end - overlap)

    return chunks