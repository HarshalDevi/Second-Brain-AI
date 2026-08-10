import re
import ssl

import httpx
from bs4 import BeautifulSoup, Tag

BOILERPLATE_SELECTORS = [
    "script",
    "style",
    "noscript",
    "nav",
    "header",
    "footer",
    "aside",
    "form",
    "button",
    "iframe",
    "svg",
    "figure",
    "figcaption",
    "sup.reference",
    ".reference",
    ".reflist",
    ".mw-editsection",
    ".mw-empty-elt",
    ".mw-jump-link",
    ".mw-portlet",
    ".mw-sidebar",
    ".mw-footer",
    ".mw-header",
    ".vector-header",
    ".vector-page-toolbar",
    ".vector-toc",
    ".vector-sticky-header",
    ".navbox",
    ".infobox",
    ".metadata",
    ".ambox",
    ".hatnote",
    ".shortdescription",
    ".toc",
    "#toc",
    "#siteNotice",
    "#mw-navigation",
    "#mw-head",
    "#mw-panel",
    "#footer",
    "#catlinks",
]

CONTENT_SELECTORS = [
    "main article",
    "article",
    "main",
    "#mw-content-text .mw-parser-output",
    "#bodyContent",
    "#content",
]

NOISY_LINE_PATTERNS = [
    re.compile(r"^\s*(toggle the table of contents|contents|references|external links|see also)\s*$", re.I),
    re.compile(r"^\s*(article|talk|read|view source|view history|tools)\s*$", re.I),
    re.compile(r"^\s*(what links here|related changes|upload file|special pages|permanent link)\b", re.I),
    re.compile(r"^\s*(page information|cite this page|get shortened url|download as pdf|printable version)\b", re.I),
    re.compile(r"^\s*(languages?|appearance|hide|edit links?)\s*$", re.I),
    re.compile(r"^\s*\d+\s+languages\b", re.I),
]


def _clean_line(line: str) -> str:
    line = re.sub(r"\[\s*\d+\s*\]", " ", line)
    line = re.sub(r"\s+([,.;:!?])", r"\1", line)
    line = re.sub(r"[ \t]+", " ", line)
    return line.strip()


def _is_noisy_line(line: str) -> bool:
    if not line:
        return True
    if any(pattern.search(line) for pattern in NOISY_LINE_PATTERNS):
        return True
    if len(line) <= 2 and not line.isalnum():
        return True
    return False


def _clean_text(text: str) -> str:
    lines = [_clean_line(line) for line in text.splitlines()]
    kept = [line for line in lines if not _is_noisy_line(line)]
    text = "\n".join(kept)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _remove_boilerplate(soup: BeautifulSoup) -> None:
    for selector in BOILERPLATE_SELECTORS:
        for tag in soup.select(selector):
            tag.decompose()

    for tag in soup.find_all(attrs={"role": ["navigation", "banner", "contentinfo", "search"]}):
        tag.decompose()


def _best_content_root(soup: BeautifulSoup) -> Tag | BeautifulSoup:
    for selector in CONTENT_SELECTORS:
        root = soup.select_one(selector)
        if root and root.get_text(strip=True):
            return root
    return soup.body or soup


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
    _remove_boilerplate(soup)

    title = soup.title.string.strip() if soup.title and soup.title.string else None
    root = _best_content_root(soup)
    text = root.get_text("\n")
    return title, _clean_text(text)