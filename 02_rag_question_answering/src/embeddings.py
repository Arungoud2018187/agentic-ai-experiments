"""Embedding layer for the RAG experiment.

Uses ``sentence-transformers`` (all-MiniLM-L6-v2) when it is installed.
A dependency-light hashing embedder is used otherwise so the experiment
can be executed on any machine without downloading a model.
"""

import hashlib
import re

import numpy as np

MODEL_NAME = "all-MiniLM-L6-v2"
HASH_DIMENSION = 512

_WORD_RE = re.compile(r"[a-z0-9]+")


def _tokens(text):
    words = _WORD_RE.findall(text.lower())
    bigrams = [f"{a}_{b}" for a, b in zip(words, words[1:])]
    return words + bigrams


def _hash_vector(text):
    vector = np.zeros(HASH_DIMENSION, dtype=np.float32)
    tokens = _tokens(text)
    if not tokens:
        return vector

    for token in tokens:
        digest = hashlib.md5(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "little") % HASH_DIMENSION
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        # Sub-linear term frequency keeps long chunks comparable.
        vector[index] += sign

    return vector


class EmbeddingModel:

    def __init__(self):
        self.backend = "hashing"
        self.model = None

        try:
            from sentence_transformers import SentenceTransformer

            print(f"Loading embedding model: {MODEL_NAME} ...")
            self.model = SentenceTransformer(MODEL_NAME)
            self.backend = "sentence-transformers"
        except Exception as error:  # noqa: BLE001 - optional dependency
            print(
                "sentence-transformers is not available "
                f"({type(error).__name__}); using the offline hashing embedder."
            )

    def encode(self, texts):
        if isinstance(texts, str):
            texts = [texts]

        if self.model is not None:
            embeddings = self.model.encode(
                texts,
                convert_to_numpy=True,
            ).astype("float32")
            return embeddings

        return np.vstack([_hash_vector(text) for text in texts]).astype("float32")

    def normalize(self, embeddings):
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return embeddings / norms
