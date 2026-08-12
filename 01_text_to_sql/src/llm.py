import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen3:8b"


def ask_llm(prompt: str) -> str:

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=120
    )

    response.raise_for_status()

    data = response.json()

    return data["response"]