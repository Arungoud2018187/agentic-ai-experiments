"""Knowledge-base retrieval with a compact BM25 index and extractive answers."""

import json
import math
import re
from collections import Counter
from pathlib import Path

from app.config import settings

_WORD_RE = re.compile(r"[a-z0-9]+")
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "can", "do", "does", "for", "from",
    "has", "have", "how", "i", "in", "is", "it", "of", "on", "or", "our", "that", "the",
    "their", "this", "to", "was", "we", "what", "when", "where", "which", "who", "why",
    "will", "with", "you", "your", "about", "tell", "me", "please", "give", "show",
}

K1 = 1.5
B = 0.75


def _normalize(token):
    if len(token) > 4 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 3 and token.endswith("s") and not token.endswith(("ss", "us", "is")):
        return token[:-1]
    return token


def unigrams(text):
    return [_normalize(word) for word in _WORD_RE.findall(text.lower()) if word not in STOPWORDS]


class KnowledgeBase:
    def __init__(self, path=None):
        self.path = Path(path or settings.knowledge_base_path)
        self.documents = []
        self.chunks = []
        self.term_frequencies = []
        self.doc_lengths = []
        self.postings = {}
        self.idf = {}
        self.average_length = 1.0
        self.load()

    def load(self):
        if not self.path.exists():
            self.documents = []
            self.chunks = []
            return

        self.documents = json.loads(self.path.read_text(encoding="utf-8"))
        self.chunks = []
        for document in self.documents:
            paragraphs = [item.strip() for item in document.get("content", "").split("\n\n") if item.strip()]
            for index, paragraph in enumerate(paragraphs, start=1):
                self.chunks.append(
                    {
                        "id": f"{document['id']}-{index}",
                        "doc_id": document["id"],
                        "title": document.get("title", document["id"]),
                        "category": document.get("category", "General"),
                        "tags": document.get("tags", []),
                        "text": paragraph,
                    }
                )

        self.term_frequencies = [Counter(unigrams(chunk["text"])) for chunk in self.chunks]
        self.doc_lengths = [sum(frequencies.values()) for frequencies in self.term_frequencies]
        self.average_length = sum(self.doc_lengths) / len(self.doc_lengths) if self.doc_lengths else 1.0
        self.postings = {}
        for index, frequencies in enumerate(self.term_frequencies):
            for term, count in frequencies.items():
                self.postings.setdefault(term, []).append((index, count))

        total = len(self.chunks)
        self.idf = {
            term: math.log(1 + (total - len(items) + 0.5) / (len(items) + 0.5))
            for term, items in self.postings.items()
        }

    @property
    def count(self):
        return len(self.documents)

    @property
    def chunk_count(self):
        return len(self.chunks)

    def _score_chunks(self, query):
        scores = [0.0] * len(self.chunks)
        query_terms = set(unigrams(query))

        for term in query_terms:
            if term not in self.postings:
                continue
            idf = self.idf[term]
            for index, frequency in self.postings[term]:
                length = self.doc_lengths[index] or 1
                denominator = frequency + K1 * (1 - B + B * length / self.average_length)
                scores[index] += idf * (frequency * (K1 + 1) / denominator)

        for index, chunk in enumerate(self.chunks):
            title_terms = set(unigrams(chunk["title"]))
            category_terms = set(unigrams(chunk["category"]))
            tag_terms = set(unigrams(" ".join(chunk.get("tags", []))))
            scores[index] += 1.8 * len(query_terms & title_terms)
            scores[index] += 0.5 * len(query_terms & category_terms)
            scores[index] += 1.4 * len(query_terms & tag_terms)

        return scores

    def search(self, query, top_k=3):
        if not self.chunks:
            return []
        scores = self._score_chunks(query)
        order = sorted(range(len(scores)), key=lambda index: scores[index], reverse=True)[:top_k]
        results = []
        for index in order:
            chunk = self.chunks[index]
            results.append(
                {
                    "id": chunk["id"],
                    "doc_id": chunk["doc_id"],
                    "title": chunk["title"],
                    "category": chunk["category"],
                    "text": chunk["text"],
                    "score": round(scores[index], 4),
                }
            )
        return results

    def answer(self, query, top_k=3):
        matches = self.search(query, top_k=top_k)
        if not matches:
            return {
                "answer": "The knowledge base is empty or unavailable.",
                "sources": [],
                "chunks": [],
                "confidence": 0.0,
            }

        # Include the rest of the top document so answers are not limited to
        # whichever paragraph happened to match the question most strongly.
        scores = self._score_chunks(query)
        answer_matches = [(match, rank) for rank, match in enumerate(matches)]
        top_doc = matches[0]["doc_id"]
        known_ids = {match["id"] for match in matches}
        for index, chunk in enumerate(self.chunks):
            if chunk["doc_id"] != top_doc or chunk["id"] in known_ids:
                continue
            answer_matches.append(
                (
                    {
                        "id": chunk["id"],
                        "doc_id": chunk["doc_id"],
                        "title": chunk["title"],
                        "category": chunk["category"],
                        "text": chunk["text"],
                        "score": round(scores[index], 4),
                    },
                    0,
                )
            )

        query_terms = set(unigrams(query))
        candidates = []
        for match, rank in answer_matches:
            for position, sentence in enumerate(_SENTENCE_RE.split(match["text"])):
                sentence = sentence.strip()
                if not sentence:
                    continue
                terms = set(_WORD_RE.findall(sentence.lower()))
                overlap = len(query_terms & terms)
                quality = min(max(0.0, match["score"]), 5.0) * 0.4
                score = overlap * 1.5 + quality - position * 0.03 - rank * 0.08
                candidates.append((score, rank, position, sentence, match))

        candidates.sort(key=lambda item: item[0], reverse=True)
        chunk_order = {chunk["id"]: index for index, chunk in enumerate(self.chunks)}
        by_chunk = {}
        for score, rank, position, sentence, match in candidates:
            by_chunk.setdefault(match["id"], []).append((score, position, sentence, match))

        top_chunks = sorted(
            {match["id"]: match for match, _ in answer_matches if match["doc_id"] == top_doc}.values(),
            key=lambda chunk: chunk_order.get(chunk["id"], 0),
        )

        selected = []
        seen_text = set()

        def add(sentence, position, match):
            key = sentence.lower()
            if key in seen_text or len(selected) >= 5:
                return
            seen_text.add(key)
            selected.append((chunk_order.get(match["id"], 0), position, sentence, match))

        # Cover every paragraph of the best-matching document first.
        for chunk in top_chunks:
            ranked = sorted(by_chunk.get(chunk["id"], []), key=lambda item: item[0], reverse=True)
            if ranked:
                score, position, sentence, match = ranked[0]
                add(sentence, position, match)

        # Add a supporting second sentence from each paragraph.
        for chunk in top_chunks:
            ranked = sorted(by_chunk.get(chunk["id"], []), key=lambda item: item[0], reverse=True)
            if len(ranked) > 1:
                score, position, sentence, match = ranked[1]
                add(sentence, position, match)

        # Fill remaining slots with the strongest sentences from other documents.
        for score, rank, position, sentence, match in candidates:
            if len(selected) >= 5:
                break
            add(sentence, position, match)

        if not selected:
            selected = [(0, 0, sentence, matches[0]) for sentence in _SENTENCE_RE.split(matches[0]["text"])[:2]]

        selected.sort(key=lambda item: (item[0], item[1]))
        answer = " ".join(item[2] for item in selected).strip()
        if len(answer) > 750:
            answer = answer[:747].rsplit(" ", 1)[0] + "..."

        sources = []
        seen_docs = set()
        for match in matches:
            if match["doc_id"] in seen_docs:
                continue
            seen_docs.add(match["doc_id"])
            sources.append(
                {
                    "type": "knowledge_base",
                    "id": match["doc_id"],
                    "title": match["title"],
                    "category": match["category"],
                    "score": match["score"],
                    "snippet": match["text"][:180].strip(),
                }
            )

        top_score = max(0.0, matches[0]["score"])
        confidence = round(min(0.97, 0.5 + top_score / 25.0), 3)
        return {
            "answer": answer,
            "sources": sources,
            "chunks": [
                {
                    "id": match["id"],
                    "title": match["title"],
                    "score": match["score"],
                    "text": match["text"][:400],
                }
                for match in matches
            ],
            "confidence": confidence,
        }


knowledge_base = KnowledgeBase()
