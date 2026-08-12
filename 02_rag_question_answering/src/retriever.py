import faiss
import numpy as np


class VectorRetriever:

    def __init__(self, embedding_model):

        self.embedding_model = embedding_model

        self.index = None
        self.documents = []

    def build_index(self, chunks):

        self.documents = chunks

        texts = [
            chunk["text"]
            for chunk in chunks
        ]

        embeddings = self.embedding_model.encode(
            texts
        )

        embeddings = self.embedding_model.normalize(
            embeddings
        )

        dimension = embeddings.shape[1]

        self.index = faiss.IndexFlatIP(
            dimension
        )

        self.index.add(embeddings)

        print(
            f"Vector database created with {len(chunks)} chunks."
        )

    def search(self, query, top_k=3):

        query_embedding = self.embedding_model.encode(
            [query]
        )

        query_embedding = self.embedding_model.normalize(
            query_embedding
        )

        scores, indices = self.index.search(
            query_embedding,
            top_k
        )

        results = []

        for score, index in zip(
            scores[0],
            indices[0]
        ):

            if index == -1:
                continue

            document = self.documents[index]

            results.append({
                "text": document["text"],
                "source": document["source"],
                "score": float(score)
            })

        return results