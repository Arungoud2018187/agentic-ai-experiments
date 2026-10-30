"""Experiment 2 - Retrieval Augmented Generation (RAG) Q&A system.

Pipeline: load documents -> chunk -> embed -> index -> retrieve -> generate.

Usage
-----
    python main.py                # interactive
    python main.py --demo         # built-in lab questions
    python main.py --question "What is RAG?"
"""

import argparse
import json
from pathlib import Path

from src.chunker import create_chunks
from src.embeddings import EmbeddingModel
from src.generator import generate_answer
from src.loader import load_documents
from src.retriever import VectorRetriever

DEMO_QUESTIONS = [
    "What is agentic AI?",
    "How does Retrieval Augmented Generation work?",
    "Why can large language models generate incorrect information?",
    "What are the benefits of running models locally?",
]

RESULT_DIR = Path(__file__).resolve().parent / "results"


def build_pipeline(data_directory="data"):
    print("=" * 60)
    print("        RAG QUESTION ANSWERING SYSTEM")
    print("=" * 60)

    print("\nLoading documents...")
    documents = load_documents(data_directory)
    print(f"Loaded {len(documents)} documents.")

    print("\nCreating chunks...")
    chunks = create_chunks(documents)
    print(f"Created {len(chunks)} chunks.")

    embedding_model = EmbeddingModel()
    retriever = VectorRetriever(embedding_model)
    retriever.build_index(chunks)

    return retriever


def answer(retriever, question, top_k=3):
    results = retriever.search(question, top_k=top_k)

    print("\nRetrieved sources:")
    for result in results:
        print(f"- {result['source']} (score: {result['score']:.3f})")

    print("\nGenerating answer...")
    return results, generate_answer(question, results)


def run_batch(questions, top_k, output_path):
    retriever = build_pipeline()
    print("\nRAG system ready.")

    records = []
    for question in questions:
        print("\n" + "=" * 60)
        print(f"QUESTION: {question}")
        print("=" * 60)

        results, generated = answer(retriever, question, top_k=top_k)

        print("\nAnswer:")
        print("-" * 60)
        print(generated)

        records.append(
            {
                "question": question,
                "answer": generated,
                "sources": [
                    {"source": item["source"], "score": round(item["score"], 4)}
                    for item in results
                ],
            }
        )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(records, indent=2), encoding="utf-8")
    print(f"\nSaved JSON results to {output_path}")
    return records


def interactive():
    retriever = build_pipeline()
    print("\nRAG system ready. Type 'exit' to quit.")

    while True:
        question = input("\nAsk a question: ").strip()
        if question.lower() == "exit":
            print("Exiting...")
            break
        if not question:
            continue

        try:
            results, generated = answer(retriever, question)
            print("\nAnswer:")
            print("-" * 60)
            print(generated)
        except Exception as error:  # noqa: BLE001
            print(f"\nERROR: {error}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--question", action="append", default=[])
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument(
        "--output",
        default=str(RESULT_DIR / "rag_results.json"),
    )
    args = parser.parse_args()

    if args.demo or args.question:
        run_batch(args.question or DEMO_QUESTIONS, args.top_k, args.output)
    else:
        interactive()


if __name__ == "__main__":
    main()
