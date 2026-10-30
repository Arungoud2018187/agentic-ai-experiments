"""Experiment 8 - Image Retrieval / Visual QA System.

Builds a visual index over a generated demo image set, classifies each
image (colour, shape, object count) and answers natural-language
questions with evidence.

Usage:
    python main.py
    python main.py --question "How many shapes are in image 6?"
    python main.py --similar images/01_red_circle.png
"""

import argparse
import json
from pathlib import Path

from src.dataset import IMAGES_DIR, create_demo_images
from src.image_encoder import ImageEncoder
from src.qa import VisualQASystem
from src.retriever import VisualRetriever
from src.vision_model import VisionModel

DEMO_QUESTIONS = [
    "What shape is in image 1?",
    "What color is the square in image 2?",
    "How many shapes are in image 6?",
    "Which images contain a circle?",
    "Which image is most similar to image 1?",
    "What is the dominant color in image 4?",
]

RESULT_DIR = Path(__file__).resolve().parent / "results"


def evaluate_classification(documents, labels):
    correct = 0
    total = 0
    details = []

    for document in documents:
        truth = labels.get(document["filename"], {}).get("objects", [])
        predicted = [
            {"shape": item["shape"], "color": item["color"]}
            for item in document["objects"]
        ]

        truth_set = sorted((item["shape"], item["color"]) for item in truth)
        predicted_set = sorted((item["shape"], item["color"]) for item in predicted)
        match = truth_set == predicted_set

        total += 1
        correct += int(match)
        details.append(
            {
                "filename": document["filename"],
                "expected": truth_set,
                "predicted": predicted_set,
                "match": match,
            }
        )

    return {
        "accuracy": round(correct / total, 3) if total else 0.0,
        "correct": correct,
        "total": total,
        "details": details,
    }


def run(questions=None, output_dir=None):
    print("=" * 60)
    print("          IMAGE RETRIEVAL / VISUAL QA SYSTEM")
    print("=" * 60)

    labels = create_demo_images()
    print(f"\nDemo image set ready: {len(labels)} images in {IMAGES_DIR}")

    encoder = ImageEncoder()
    vision_model = VisionModel()
    retriever = VisualRetriever(encoder, vision_model)
    documents = retriever.build_index(IMAGES_DIR)

    print("\nIMAGE ANALYSIS")
    print("-" * 60)
    for index, document in enumerate(documents, start=1):
        print(f"[{index}] {document['filename']}: {document['description']}")

    evaluation = evaluate_classification(documents, labels)
    print(
        f"\nClassification accuracy: {evaluation['accuracy'] * 100:.1f}% "
        f"({evaluation['correct']}/{evaluation['total']} images)"
    )

    qa = VisualQASystem(retriever)
    records = []

    print("\nVISUAL QUESTION ANSWERING")
    print("-" * 60)
    for question in questions or DEMO_QUESTIONS:
        result = qa.answer(question)
        print(f"\nQ: {result['question']}")
        print(f"A: {result['answer']}")
        print(f"   confidence={result['confidence']}")
        records.append(result)

    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "images": documents,
            "classification_evaluation": evaluation,
            "qa": records,
        }
        (output_dir / "visual_qa_results.json").write_text(
            json.dumps(payload, indent=2), encoding="utf-8"
        )
        print(f"\nSaved results to {output_dir / 'visual_qa_results.json'}")

    return {
        "documents": documents,
        "evaluation": evaluation,
        "qa": records,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--question", action="append", default=[])
    parser.add_argument("--similar", default=None, help="find images similar to this path")
    parser.add_argument(
        "--output-dir",
        default=str(RESULT_DIR),
    )
    args = parser.parse_args()

    if args.similar:
        create_demo_images()
        retriever = VisualRetriever(ImageEncoder(), VisionModel())
        retriever.build_index(IMAGES_DIR)
        for result in retriever.search_similar(args.similar):
            print(result)
        return

    run(args.question or None, output_dir=args.output_dir)


if __name__ == "__main__":
    main()
