"""LLM client for the prompt-chaining experiment.

Provider order: Ollama -> OpenAI-compatible endpoint -> offline fallback
(handled by ``chain.py``).  Configure with the same environment variables
as the other experiments.
"""

import os

import requests

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "http://localhost:1234/v1").rstrip("/")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "local-model")
PROVIDER = os.getenv("LLM_PROVIDER", "auto").lower()
_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "120"))


class LLMUnavailable(RuntimeError):
    pass


def _ollama(prompt):
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "think": False,
            "options": {"temperature": 0.2, "num_predict": 500},
        },
        timeout=_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()["response"].strip()


def _openai(prompt):
    headers = {"Content-Type": "application/json"}
    if OPENAI_API_KEY:
        headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"
    response = requests.post(
        f"{OPENAI_BASE_URL}/chat/completions",
        headers=headers,
        json={
            "model": OPENAI_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        },
        timeout=_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


def ask_llm(prompt: str) -> str:
    if PROVIDER == "offline":
        raise LLMUnavailable("LLM_PROVIDER=offline")

    if PROVIDER in ("ollama", "auto"):
        try:
            return _ollama(prompt)
        except Exception as error:  # noqa: BLE001
            if PROVIDER == "ollama":
                raise LLMUnavailable(str(error)) from error

    if PROVIDER in ("openai", "auto"):
        if PROVIDER == "openai" or OPENAI_API_KEY:
            try:
                return _openai(prompt)
            except Exception as error:  # noqa: BLE001
                raise LLMUnavailable(str(error)) from error

    raise LLMUnavailable("No LLM provider reachable.")
