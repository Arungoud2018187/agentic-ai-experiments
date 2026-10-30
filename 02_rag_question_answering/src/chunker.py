"""Document chunking for the RAG experiment.

Chunks are built from whole sentences with a character overlap so that
retrieved context never starts or ends in the middle of a word.
"""

import re


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


def chunk_text(text, chunk_size=500, overlap=100):
    sentences = _split_sentences(text)
    if not sentences:
        return []

    chunks = []
    current = []
    current_length = 0

    for sentence in sentences:
        # A single very long sentence becomes its own chunk.
        if len(sentence) > chunk_size:
            if current:
                chunks.append(" ".join(current))
                current, current_length = [], 0
            chunks.append(sentence[:chunk_size])
            continue

        if current and current_length + len(sentence) + 1 > chunk_size:
            chunks.append(" ".join(current))

            # Build the overlap from the trailing sentences.
            overlap_sentences = []
            overlap_length = 0
            for previous in reversed(current):
                if overlap_length + len(previous) + 1 > overlap:
                    break
                overlap_sentences.insert(0, previous)
                overlap_length += len(previous) + 1

            current = overlap_sentences
            current_length = overlap_length

        current.append(sentence)
        current_length += len(sentence) + 1

    if current:
        chunks.append(" ".join(current))

    return chunks


def create_chunks(documents):
    chunks = []

    for document in documents:
        for chunk in chunk_text(document["text"]):
            chunks.append(
                {
                    "text": chunk,
                    "source": document["filename"],
                }
            )

    return chunks
