"""Visual question answering.

The QA layer parses a question, locates the referenced image (or filters
the index by colour/shape), then answers from the vision model output.
"""

import re
from pathlib import Path

from src.retriever import parse_visual_terms

_COUNT_RE = re.compile(r"\bhow many\b", re.IGNORECASE)
_COLOR_RE = re.compile(r"\bcolor\b|\bcolour\b", re.IGNORECASE)
_SHAPE_RE = re.compile(r"\bwhat shape\b|\bwhich shape\b", re.IGNORECASE)
_SIMILAR_RE = re.compile(r"\bsimilar\b", re.IGNORECASE)
_IMAGE_RE = re.compile(r"\bimage\s*(\d+)\b|\b(\d+)\.(?:png|jpg|jpeg|webp)\b", re.IGNORECASE)


class VisualQASystem:
    name = "VisualQASystem"

    def __init__(self, retriever):
        self.retriever = retriever

    def _resolve_image(self, question):
        match = _IMAGE_RE.search(question)
        if match:
            index = int(match.group(1) or match.group(2))
            if 1 <= index <= len(self.retriever.paths):
                return self.retriever.paths[index - 1]

        lowered = question.lower()
        for path in self.retriever.paths:
            if path.name.lower() in lowered or path.stem.lower() in lowered:
                return path
        return None

    def _document_for(self, path):
        for document in self.retriever.documents:
            if document["filename"] == Path(path).name:
                return document
        return None

    def answer(self, question):
        image_path = self._resolve_image(question)
        document = self._document_for(image_path) if image_path else None
        color, shape = parse_visual_terms(question)

        if _COUNT_RE.search(question):
            if not document:
                return self._error(question, "Please reference an image, for example 'image 6'.")
            return self._result(
                question,
                f"Image {self._label(document)} contains {document['object_count']} shape(s): "
                + document["description"].lower().replace("the image contains ", ""),
                document,
                0.95,
            )

        if _SIMILAR_RE.search(question):
            if not document:
                return self._error(question, "Please reference an image to compare against.")
            similar = self.retriever.search_similar(image_path, top_k=2)
            if not similar:
                return self._error(question, "No similar images were found.")
            best = similar[0]
            return self._result(
                question,
                f"The most similar image is {best['filename']} "
                f"(similarity {best['score']:.3f}): {best['description']}",
                {"similar": similar},
                0.85,
            )

        if _COLOR_RE.search(question):
            if document:
                target = document["objects"][0]
                if shape:
                    match = next(
                        (item for item in document["objects"] if item["shape"] == shape),
                        target,
                    )
                    target = match
                return self._result(
                    question,
                    f"The {target['shape']} in {document['filename']} is {target['color']}.",
                    target,
                    target["confidence"],
                )
            if shape:
                matches = self.retriever.search_by_text(question)
                if matches:
                    names = ", ".join(item["filename"] for item in matches)
                    return self._result(
                        question,
                        f"Images containing a {shape}: {names}.",
                        {"matches": [item["filename"] for item in matches]},
                        0.8,
                    )
            return self._error(question, "I could not identify the referenced image or shape.")

        if _SHAPE_RE.search(question):
            if document:
                target = document["objects"][0]
                if color:
                    match = next(
                        (item for item in document["objects"] if item["color"] == color),
                        target,
                    )
                    target = match
                return self._result(
                    question,
                    f"The {target['color']} object in {document['filename']} is a {target['shape']}.",
                    target,
                    target["confidence"],
                )
            return self._error(question, "Please reference an image, for example 'image 3'.")

        if "which image" in question.lower() or "find" in question.lower():
            matches = self.retriever.search_by_text(question)
            if not matches:
                return self._error(question, "No images matched that description.")
            names = ", ".join(
                f"{item['filename']} ({item['description'].lower()})" for item in matches
            )
            return self._result(
                question,
                f"Matching images: {names}.",
                {"matches": [item["filename"] for item in matches]},
                0.85,
            )

        if document:
            return self._result(
                question,
                f"{document['filename']}: {document['description']}",
                document,
                0.8,
            )

        matches = self.retriever.search_by_text(question)
        if matches:
            names = ", ".join(item["filename"] for item in matches)
            return self._result(question, f"Relevant images: {names}.", {"matches": names}, 0.7)

        return self._error(
            question,
            "I could not answer that question. Try asking about colour, shape, count "
            "or similarity for a specific image."
        )

    def _label(self, document):
        try:
            return self.retriever.paths.index(Path(document["path"])) + 1
        except ValueError:
            return document["filename"]

    def _result(self, question, answer, evidence, confidence):
        return {
            "question": question,
            "answer": answer,
            "evidence": evidence,
            "confidence": round(confidence, 2),
        }

    def _error(self, question, message):
        return {
            "question": question,
            "answer": message,
            "evidence": {},
            "confidence": 0.0,
        }
