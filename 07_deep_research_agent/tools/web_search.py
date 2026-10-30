"""Web search tool with an offline corpus fallback.

Live mode uses DuckDuckGo's HTML endpoint.  Offline mode scores the
curated corpus in ``data/corpus.json`` by lexical overlap.  Both modes
return the same result shape so the rest of the workflow is unchanged.
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

_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "can", "do", "does",
    "for", "from", "how", "i", "in", "is", "it", "of", "on", "or", "that",
    "the", "their", "this", "to", "what", "when", "where", "which", "who",
    "why", "with", "would", "should", "could", "will", "using", "use",
}


def tokenize(text):
    return [
        word
        for word in re.findall(r"[a-z0-9]+", text.lower())
        if word not in _STOPWORDS and len(word) > 2
    ]


def load_corpus():
    return json.loads(CORPUS_PATH.read_text(encoding="utf-8"))


def _snippet(text, terms, length=320):
    sentences = re.split(r"(?<=[.!?])\s+", text)
    ranked = sorted(
        sentences,
        key=lambda sentence: sum(term in sentence.lower() for term in terms),
        reverse=True,
    )
    snippet = ranked[0] if ranked else text[:length]
    return snippet[:length].strip()


class WebSearchTool:
    name = "web_search"

    def __init__(self, offline=True):
        self.offline = offline
        self.corpus = load_corpus()
        self.calls = []

    def search(self, query, max_results=5):
        self.calls.append({"query": query, "mode": "offline" if self.offline else "live"})

        if not self.offline:
            try:
                results = self._live_search(query, max_results)
                if results:
                    return results
            except Exception:  # noqa: BLE001 - fall back to corpus
                pass

        return self._offline_search(query, max_results)

    def _offline_search(self, query, max_results):
        terms = tokenize(query)
        results = []

        for document in self.corpus:
            haystack = " ".join(
                [document["title"], document["text"], " ".join(document["tags"])]
            ).lower()
            score = sum(haystack.count(term) for term in terms)

            # Title and tag matches carry extra weight.
            score += 2 * sum(term in document["title"].lower() for term in terms)
            score += 2 * sum(term in " ".join(document["tags"]).lower() for term in terms)

            if score <= 0:
                continue

            results.append(
                {
                    "doc_id": document["id"],
                    "title": document["title"],
                    "url": document["url"],
                    "snippet": _snippet(document["text"], terms),
                    "score": score,
                    "source": "local corpus",
                }
            )

        results.sort(key=lambda item: item["score"], reverse=True)
        return results[:max_results]

    def _live_search(self, query, max_results):
        import requests
        from bs4 import BeautifulSoup

        response = requests.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            headers={"User-Agent": _UA},
            timeout=15,
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        results = []

        for result in soup.select(".result"):
            link = result.select_one(".result__a")
            snippet = result.select_one(".result__snippet")
            if not link:
                continue

            href = link.get("href", "")
            if "uddg=" in href:
                from urllib.parse import parse_qs, urlparse

                href = parse_qs(urlparse(href).query).get("uddg", [href])[0]

            results.append(
                {
                    "doc_id": href,
                    "title": link.get_text(" ", strip=True),
                    "url": href,
                    "snippet": snippet.get_text(" ", strip=True) if snippet else "",
                    "score": 1.0,
                    "source": "DuckDuckGo",
                }
            )
            if len(results) >= max_results:
                break

        return results
