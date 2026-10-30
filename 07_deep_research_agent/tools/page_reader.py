"""Page reader tool.

Reads a local corpus document or fetches and cleans an HTTP page with
BeautifulSoup.  The returned shape is identical for both paths.
"""

import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CORPUS_PATH = BASE_DIR / "data" / "corpus.json"

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


class PageReaderTool:
    name = "page_reader"

    def __init__(self, offline=True):
        self.offline = offline
        self.corpus = {
            document["id"]: document
            for document in json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
        }
        self.calls = []

    def read(self, result):
        """Read a search result. Accepts a dict or a local:// URL."""

        if isinstance(result, str):
            result = {"url": result, "doc_id": result, "title": result}

        url = result.get("url", "")

        if self.offline or url.startswith("local://"):
            return self._read_local(result)

        try:
            return self._read_web(url, result.get("title", url))
        except Exception:  # noqa: BLE001 - fall back to local corpus
            return self._read_local(result)

    def _read_local(self, result):
        document = self.corpus.get(result.get("doc_id"))
        if document is None:
            document = next(
                (
                    item
                    for item in self.corpus.values()
                    if item["url"] == result.get("url")
                ),
                None,
            )

        if document is None:
            return {
                "title": result.get("title", "Untitled"),
                "url": result.get("url", ""),
                "text": result.get("snippet", ""),
                "source": "search snippet",
            }

        self.calls.append({"url": document["url"], "mode": "local"})
        return {
            "title": document["title"],
            "url": document["url"],
            "text": document["text"],
            "source": "local corpus",
        }

    def _read_web(self, url, title):
        import requests
        from bs4 import BeautifulSoup

        response = requests.get(url, headers={"User-Agent": _UA}, timeout=20)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "form"]):
            tag.decompose()

        text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))

        self.calls.append({"url": url, "mode": "web"})
        return {
            "title": soup.title.get_text(strip=True) if soup.title else title,
            "url": url,
            "text": text[:8000],
            "source": "web",
        }
