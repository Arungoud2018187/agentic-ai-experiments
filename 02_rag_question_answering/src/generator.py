"""Answer generation for the RAG experiment.

The preferred path sends retrieved context to a local Ollama model.  If
no model server is available, an extractive answer is composed from the
highest-scoring context sentences so the pipeline still produces a
grounded, source-cited answer offline.
"""

import re
from collections import Counter

import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen3:8b"

_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "can", "do", "does",
    "for", "from", "how", "i", "in", "is", "it", "of", "on", "or", "that",
    "the", "their", "this", "to", "what", "when", "where", "which", "who",
    "why", "with", "system", "systems",
}


def _tokens(text):
    return [
        word for word in re.findall(r"[a-z0-9]+", text.lower())
        if word not in _STOPWORDS and len(word) > 2
    ]


def _split_sentences(text):
    sentences = []
    for block in re.split(r"\n\s*\n", text):
        block = re.sub(r"\s+", " ", block).strip()
        if not block:
            continue
        sentences.extend(
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", block)
            if sentence.strip()
        )
    return sentences


def generate_answer_offline(question, retrieved_documents):
    """Extractive, grounded answer with citations."""

    question_terms = set(_tokens(question))
    if not question_terms:
        question_terms = set(re.findall(r"[a-z0-9]+", question.lower()))

    candidates = []
    seen = set()

    for document in retrieved_documents:
        for sentence in _split_sentences(document["text"]):
            normalized = sentence.lower()
            if normalized in seen:
                continue
            seen.add(normalized)

            # Skip headings and fragments that carry no real content.
            if len(sentence.split()) < 6:
                continue

            sentence_terms = Counter(_tokens(sentence))
            overlap = sum(sentence_terms[term] for term in question_terms)

            # Normalise by length so very long sentences do not dominate.
            score = overlap / (len(sentence_terms) ** 0.5 + 1e-6)

            if overlap:
                candidates.append((score, sentence, document["source"]))

    if not candidates:
        return (
            "I don't have enough information in the provided documents.\n\n"
            "Retrieved context:\n"
            + "\n".join(
                f"- {doc['source']}: {doc['text'][:200]}..." for doc in retrieved_documents
            )
        )

    candidates.sort(key=lambda item: item[0], reverse=True)

    selected = []
    sources = []
    for _, sentence, source in candidates[:3]:
        if sentence not in selected:
            selected.append(sentence)
            if source not in sources:
                sources.append(source)

    answer = " ".join(selected)
    return f"{answer}\n\nSources: {', '.join(sources)}"


def generate_answer(question, retrieved_documents):
    context = "\n\n".join(
        f"Source: {doc['source']}\n{doc['text']}" for doc in retrieved_documents
    )

    prompt = f"""
You are a question-answering assistant.

Answer the user's question using ONLY the provided context.

If the answer cannot be found in the context, say:
"I don't have enough information in the provided documents."

Do not invent information. Cite the source file names.

CONTEXT:
{context}

QUESTION:
{question}

ANSWER:
"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": MODEL, "prompt": prompt, "stream": False},
            timeout=120,
        )
        response.raise_for_status()
        return response.json()["response"].strip()
    except Exception:  # noqa: BLE001 - offline fallback
        return generate_answer_offline(question, retrieved_documents)
