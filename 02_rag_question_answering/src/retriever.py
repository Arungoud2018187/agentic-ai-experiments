"""Vector retriever for the RAG experiment.

Uses FAISS when installed, otherwise falls back to an exact cosine
similarity search with NumPy.  Both paths produce the same result shape.
"""

import numpy as np


class VectorRetriever:

    def __init__(self, embedding_model):
        self.embedding_model = embedding_model
        self.index = None
        self.matrix = None
        self.documents = []
        self.backend = "numpy"

    def build_index(self, chunks):
        self.documents = chunks

        texts = [chunk["text"] for chunk in chunks]
        embeddings = self.embedding_model.encode(texts)
        embeddings = self.embedding_model.normalize(embeddings).astype("float32")

        try:
            import faiss

            self.index = faiss.IndexFlatIP(embeddings.shape[1])
            self.index.add(embeddings)
            self.backend = "faiss"
        except Exception:  # noqa: BLE001 - optional dependency
            self.matrix = embeddings

        print(
            f"Vector database created with {len(chunks)} chunks "
            f"(backend: {self.backend})."
        )

    def search(self, query, top_k=3):
        query_embedding = self.embedding_model.encode([query])
        query_embedding = self.embedding_model.normalize(query_embedding)
        query_embedding = query_embedding.astype("float32")

        top_k = min(top_k, len(self.documents))

        if self.index is not None:
            scores, indices = self.index.search(query_embedding, top_k)
            scores, indices = scores[0], indices[0]
        else:
            scores_all = (self.matrix @ query_embedding[0])
            indices = np.argsort(-scores_all)[:top_k]
            scores = scores_all[indices]

        results = []
        for score, index in zip(scores, indices):
            if index == -1:
                continue

            document = self.documents[int(index)]
            results.append(
                {
                    "text": document["text"],
                    "source": document["source"],
                    "score": float(score),
                }
            )

        return results
