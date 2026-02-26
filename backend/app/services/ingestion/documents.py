from pathlib import Path
from pypdf import PdfReader


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

    if suffix in [".md", ".txt"]:
        return p.read_text(encoding="utf-8", errors="ignore").strip()

    # fallback: try read as utf-8
    return p.read_text(encoding="utf-8", errors="ignore").strip()