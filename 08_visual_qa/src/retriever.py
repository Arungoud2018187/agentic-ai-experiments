"""Visual retriever.

Combines a feature-vector index (for image-to-image similarity) with
metadata filters (for text questions such as "blue square").
"""

import re

import numpy as np

_COLORS = {"red", "blue", "green", "yellow", "purple", "orange", "teal", "black", "gray", "white"}
_SHAPES = {"circle", "square", "rectangle", "triangle", "star"}


def parse_visual_terms(text):
    lowered = text.lower()
    color = next((item for item in _COLORS if item in lowered), None)
    shape = next((item for item in _SHAPES if item in lowered), None)
    return color, shape


class VisualRetriever:
    name = "VisualRetriever"

    def __init__(self, encoder, vision_model):
        self.encoder = encoder
        self.vision_model = vision_model
        self.paths = []
        self.vectors = None
        self.documents = []

    def build_index(self, images_dir):
        from pathlib import Path

        self.paths = sorted(
            path
            for path in Path(images_dir).glob("*")
            if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
        )
        self.vectors = self.encoder.encode_many(self.paths)
        self.documents = [self.vision_model.analyze(path) for path in self.paths]

        print(f"Visual index built with {len(self.paths)} images.")
        return self.documents

    def search_similar(self, image_path, top_k=3):
        query = self.encoder.encode(image_path)
        scores = self.vectors @ query
        order = np.argsort(-scores)

        results = []
        for index in order:
            if str(self.paths[int(index)]) == str(image_path):
                continue
            results.append(
                {
                    "filename": self.paths[int(index)].name,
                    "score": round(float(scores[int(index)]), 4),
                    "description": self.documents[int(index)]["description"],
                }
            )
            if len(results) >= top_k:
                break
        return results

    def search_by_text(self, text, top_k=5):
        color, shape = parse_visual_terms(text)
        scored = []

        for document in self.documents:
            score = 0
            for item in document["objects"]:
                if color and item["color"] == color:
                    score += 2
                if shape and item["shape"] == shape:
                    score += 2
            if score:
                scored.append((score, document))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [document for _, document in scored[:top_k]]
