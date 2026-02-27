import re
import ssl
import httpx
from bs4 import BeautifulSoup


def _clean_text(t: str) -> str:
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


# Railway-safe SSL context
_ssl_context = ssl.create_default_context()
_ssl_context.check_hostname = False
_ssl_context.verify_mode = ssl.CERT_NONE


async def fetch_and_extract_url(url: str) -> tuple[str | None, str]:
    """
    Returns (title, text)
    """
    async with httpx.AsyncClient(
        timeout=20,
        follow_redirects=True,
        verify=_ssl_context,
    ) as client:
        r = await client.get(
            url,
            headers={"User-Agent": "SecondBrainBot/0.1"},
        )
        r.raise_for_status()
        html = r.text

    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    title = soup.title.string.strip() if soup.title and soup.title.string else None
    text = soup.get_text("\n")

    return title, _clean_text(text)