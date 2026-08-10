import re
from dataclasses import dataclass


@dataclass
class Chunk:
    index: int
    text: str
    token_count: int | None = None


def normalize_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _split_units(text: str) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    units: list[str] = []

    for paragraph in paragraphs:
        if len(paragraph) <= 700:
            units.append(paragraph)
            continue

        sentences = re.split(r"(?<=[.!?])\s+", paragraph)
        buffer: list[str] = []
        current_len = 0
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            if current_len and current_len + len(sentence) + 1 > 700:
                units.append(" ".join(buffer))
                buffer = [sentence]
                current_len = len(sentence)
            else:
                buffer.append(sentence)
                current_len += len(sentence) + (1 if current_len else 0)
        if buffer:
            units.append(" ".join(buffer))

    return units


def _tail_sentences(text: str, max_chars: int) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    tail: list[str] = []
    total = 0
    for sentence in reversed(sentences):
        if not sentence:
            continue
        extra = len(sentence) + (1 if tail else 0)
        if tail and total + extra > max_chars:
            break
        tail.append(sentence)
        total += extra
    return " ".join(reversed(tail)).strip()


def chunk_text(text: str, max_chars: int = 1400, overlap: int = 220) -> list[Chunk]:
    """Create chunks on paragraph/sentence boundaries with light semantic overlap."""
    text = normalize_text(text)
    if not text:
        return []

    units = _split_units(text)
    chunks: list[Chunk] = []
    current: list[str] = []
    current_len = 0

    for unit in units:
        separator_len = 2 if current else 0
        if current and current_len + separator_len + len(unit) > max_chars:
            chunk = "\n\n".join(current).strip()
            chunks.append(Chunk(index=len(chunks), text=chunk))

            overlap_text = _tail_sentences(chunk, overlap)
            current = [overlap_text] if overlap_text else []
            current_len = len(overlap_text)

        if len(unit) > max_chars:
            start = 0
            while start < len(unit):
                end = min(start + max_chars, len(unit))
                segment = unit[start:end].strip()
                if segment:
                    if current:
                        chunks.append(Chunk(index=len(chunks), text="\n\n".join(current).strip()))
                        current = []
                        current_len = 0
                    chunks.append(Chunk(index=len(chunks), text=segment))
                if end == len(unit):
                    break
                start = max(0, end - overlap)
            continue

        current.append(unit)
        current_len += len(unit) + (2 if current_len else 0)

    if current:
        chunks.append(Chunk(index=len(chunks), text="\n\n".join(current).strip()))

    return chunks