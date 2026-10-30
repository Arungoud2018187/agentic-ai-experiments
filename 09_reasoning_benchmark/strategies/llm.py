"""Optional LLM access for the reasoning strategies.

Offline mode (default) uses the deterministic solver so benchmark
results are reproducible.  Set ``USE_LLM=1`` and configure Ollama to
compare the prompting strategies against a real model.
"""

import os

import requests

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")
USE_LLM = os.getenv("USE_LLM", "0") == "1"


def ask_llm(prompt, timeout=90):
    if not USE_LLM:
        return None

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "think": False,
                "options": {"temperature": 0.0, "num_predict": 300},
            },
            timeout=timeout,
        )
        response.raise_for_status()
        return response.json()["response"].strip()
    except Exception:  # noqa: BLE001 - fall back to solver
        return None


def first_line(text):
    if not text:
        return None
    return text.strip().splitlines()[0].strip()
