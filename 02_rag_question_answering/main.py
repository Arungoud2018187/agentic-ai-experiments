from src.loader import load_documents
from src.chunker import create_chunks
from src.embeddings import EmbeddingModel
from src.retriever import VectorRetriever
from src.generator import generate_answer


def main():

    print("=" * 60)
    print("        RAG QUESTION ANSWERING SYSTEM")
    print("=" * 60)

    # ----------------------------
    # Load documents
    # ----------------------------

    print("\nLoading documents...")

    documents = load_documents("data")

    print(
        f"Loaded {len(documents)} documents."
    )

    # ----------------------------
    # Create chunks
    # ----------------------------

    print("\nCreating chunks...")

    chunks = create_chunks(documents)

    print(
        f"Created {len(chunks)} chunks."
    )

    # ----------------------------
    # Embedding model
    # ----------------------------

    embedding_model = EmbeddingModel()

    # ----------------------------
    # Build vector database
    # ----------------------------

    retriever = VectorRetriever(
        embedding_model
    )

    retriever.build_index(chunks)

    print("\nRAG system ready.")

    print("Type 'exit' to quit.")

    # ----------------------------
    # Question answering
    # ----------------------------

    while True:

        question = input(
            "\nAsk a question: "
        ).strip()

        if question.lower() == "exit":

            print("Exiting...")

            break

        if not question:
            continue

        # Retrieve relevant chunks

        print("\nRetrieving relevant information...")

        results = retriever.search(
            question,
            top_k=3
        )

        print("\nRetrieved sources:")

        for result in results:

            print(
                f"- {result['source']} "
                f"(score: {result['score']:.3f})"
            )

        # Generate answer

        print("\nGenerating answer...")

        answer = generate_answer(
            question,
            results
        )

        print("\nAnswer:")
        print("-" * 60)
        print(answer)


if __name__ == "__main__":
    main()