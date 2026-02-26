import re
import httpx
from bs4 import BeautifulSoup


def _clean_text(t: str) -> str:
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


async def fetch_and_extract_url(url: str) -> tuple[str | None, str]:
    """
    Returns (title, text)
    """
    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        r = await client.get(url, headers={"User-Agent": "SecondBrainBot/0.1"})
        r.raise_for_status()
        html = r.text

    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    title = soup.title.string.strip() if soup.title and soup.title.string else None
    text = soup.get_text("\n")
    return title, _clean_text(text)