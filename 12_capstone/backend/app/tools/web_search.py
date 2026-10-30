"""Simulated web-search tool backed by a small curated index.

The capstone runs offline by default. The interface mirrors a real search
API (query -> ranked results, URL -> page text) so a production adapter
can replace this module without touching the research agent.
"""

import json
import re
from pathlib import Path

from app.config import settings

_WORD_RE = re.compile(r"[a-z0-9]+")


def _tokens(text):
    return set(_WORD_RE.findall(text.lower()))


class WebSearchTool:
    def __init__(self, path=None):
        self.path = Path(path or settings.web_index_path)
        self.index = []
        self.load()

    def load(self):
        if self.path.exists():
            self.index = json.loads(self.path.read_text(encoding="utf-8"))
        else:
            self.index = []

    @property
    def count(self):
        return len(self.index)

    def search(self, query, max_results=3):
        terms = _tokens(query)
        scored = []
        for item in self.index:
            title_terms = _tokens(item.get("title", ""))
            snippet_terms = _tokens(item.get("snippet", ""))
            content_terms = _tokens(item.get("content", ""))
            score = len(terms & title_terms) * 3.0
            score += len(terms & snippet_terms) * 2.0
            score += len(terms & content_terms) * 1.0
            if query.lower().strip() and query.lower().strip() in item.get("title", "").lower():
                score += 4.0
            if score > 0:
                scored.append((score, item))

        scored.sort(key=lambda pair: pair[0], reverse=True)
        results = []
        for score, item in scored[:max_results]:
            results.append(
                {
                    "id": item["id"],
                    "title": item["title"],
                    "url": item["url"],
                    "snippet": item["snippet"],
                    "content": item.get("content", ""),
                    "score": round(score, 2),
                    "source": "simulated_web_index",
                }
            )
        return results

    def read(self, identifier):
        for item in self.index:
            if identifier in (item.get("id"), item.get("url")):
                return item
        return None

    def health(self):
        return {"status": "ready" if self.index else "empty", "documents": len(self.index)}


web_search = WebSearchTool()
