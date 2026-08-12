import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen3:8b"


def generate_answer(question, retrieved_documents):

    context = "\n\n".join(
        [
            f"Source: {doc['source']}\n{doc['text']}"
            for doc in retrieved_documents
        ]
    )

    prompt = f"""
You are a question-answering assistant.

Answer the user's question using ONLY the provided context.

If the answer cannot be found in the context, say:
"I don't have enough information in the provided documents."

Do not invent information.

CONTEXT:
{context}

QUESTION:
{question}

ANSWER:
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False
        },
        timeout=120
    )

    response.raise_for_status()

    return response.json()["response"].strip()