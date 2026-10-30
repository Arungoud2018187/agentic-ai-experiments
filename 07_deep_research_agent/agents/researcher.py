"""Researcher agent.

For each sub-question the researcher searches, reads the top sources,
extracts the most relevant sentences and records citations.
"""

import re
from collections import Counter

from tools.page_reader import PageReaderTool
from tools.web_search import WebSearchTool, tokenize

_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "can", "do", "does",
    "for", "from", "how", "i", "in", "is", "it", "of", "on", "or", "that",
    "the", "their", "this", "to", "what", "when", "where", "which", "who",
    "why", "with", "would", "should", "could", "will",
}


def _sentences(text):
    return [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", text)
        if len(sentence.split()) >= 5
    ]


def _best_sentences(text, query, limit=2):
    query_terms = set(tokenize(query))
    frequencies = Counter(tokenize(text))
    scored = []

    for sentence in _sentences(text):
        terms = tokenize(sentence)
        overlap = sum(1 for term in terms if term in query_terms)
        if overlap == 0:
            continue
        score = overlap + sum(frequencies[term] for term in terms) / (
            len(terms) ** 0.5 + 1
        )
        scored.append((score, sentence))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [sentence for _, sentence in scored[:limit]]


class ResearcherAgent:
    name = "ResearcherAgent"

    def __init__(self, offline=True):
        self.search_tool = WebSearchTool(offline=offline)
        self.reader_tool = PageReaderTool(offline=offline)
        self.notes = []

    def research(self, subquestion, max_results=3):
        results = self.search_tool.search(subquestion, max_results=max_results)

        findings = []
        sources = []
        seen_sources = set()

        for result in results:
            if result.get("doc_id") in seen_sources:
                continue
            seen_sources.add(result.get("doc_id"))

            document = self.reader_tool.read(result)
            sources.append(
                {
                    "id": result.get("doc_id"),
                    "title": document["title"],
                    "url": document["url"],
                    "source": document["source"],
                }
            )

            for sentence in _best_sentences(document["text"], subquestion, limit=2):
                findings.append(
                    {
                        "text": sentence,
                        "source_id": result.get("doc_id"),
                        "title": document["title"],
                        "url": document["url"],
                    }
                )

        note = {
            "subquestion": subquestion,
            "findings": findings,
            "sources": sources,
            "result_count": len(results),
        }
        self.notes.append(note)
        return note
