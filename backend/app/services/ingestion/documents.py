from pathlib import Path

from pypdf import PdfReader

SUPPORTED_DOCUMENT_EXTENSIONS = {".pdf", ".md", ".txt"}
TEXT_EXTENSIONS = {".md", ".txt"}


def supported_document_extensions() -> set[str]:
    return set(SUPPORTED_DOCUMENT_EXTENSIONS)


def extract_text_from_file(path: str) -> str:
    p = Path(path)
    suffix = p.suffix.lower()

    if suffix == ".pdf":
        reader = PdfReader(str(p))
        parts = []
        for page in reader.pages:
            t = page.extract_text() or ""
            if t.strip():
                parts.append(t)
        return "\n\n".join(parts).strip()

    if suffix in TEXT_EXTENSIONS:
        return p.read_text(encoding="utf-8", errors="strict").strip()

    supported = ", ".join(sorted(SUPPORTED_DOCUMENT_EXTENSIONS))
    raise ValueError(f"Unsupported document type '{suffix or 'unknown'}'. Supported types: {supported}")