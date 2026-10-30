"""
LLM access layer for the Text-to-SQL experiment.

The experiment is designed to run against a local Ollama server
(https://ollama.com) but also supports any OpenAI-compatible endpoint
(LM Studio, vLLM, OpenAI, ...).  When no model server is reachable the
caller falls back to the deterministic rule-based generator in
``sql_generator.py`` so that the whole workflow can still be executed
and demonstrated offline.

Environment variables
---------------------
LLM_PROVIDER     auto | ollama | openai | offline   (default: auto)
OLLAMA_URL       default http://localhost:11434/api/generate
OLLAMA_MODEL     default qwen3:8b
OPENAI_BASE_URL  default http://localhost:1234/v1
OPENAI_API_KEY   optional
OPENAI_MODEL     default local-model
"""

import os

import requests

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434/api/generate",
)

MODEL = os.getenv(
    "OLLAMA_MODEL",
    "qwen3:8b",
)

OPENAI_BASE_URL = os.getenv(
    "OPENAI_BASE_URL",
    "http://localhost:1234/v1",
).rstrip("/")

OPENAI_API_KEY = os.getenv(
    "OPENAI_API_KEY",
    "",
)

OPENAI_MODEL = os.getenv(
    "OPENAI_MODEL",
    "local-model",
)

PROVIDER = os.getenv(
    "LLM_PROVIDER",
    "auto",
).lower()

_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "120"))


class LLMUnavailable(RuntimeError):
    """Raised when no configured model server can be reached."""


def _ask_ollama(prompt: str) -> str:
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "think": False,
            "options": {"temperature": 0.1},
        },
        timeout=_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()["response"].strip()


def _ask_openai(prompt: str) -> str:
    headers = {"Content-Type": "application/json"}
    if OPENAI_API_KEY:
        headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"

    response = requests.post(
        f"{OPENAI_BASE_URL}/chat/completions",
        headers=headers,
        json={
            "model": OPENAI_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
        },
        timeout=_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


def ask_llm(prompt: str) -> str:
    """Send a prompt to the configured provider.

    Raises ``LLMUnavailable`` when no provider is reachable.  Callers are
    expected to catch this exception and use their offline fallback.
    """

    if PROVIDER == "offline":
        raise LLMUnavailable("LLM_PROVIDER=offline")

    if PROVIDER in ("ollama", "auto"):
        try:
            return _ask_ollama(prompt)
        except Exception as error:  # noqa: BLE001 - provider probing
            if PROVIDER == "ollama":
                raise LLMUnavailable(str(error)) from error

    if PROVIDER in ("openai", "auto"):
        if PROVIDER == "openai" or OPENAI_API_KEY:
            try:
                return _ask_openai(prompt)
            except Exception as error:  # noqa: BLE001
                raise LLMUnavailable(str(error)) from error

    raise LLMUnavailable(
        "No LLM provider reachable. Start Ollama or set LLM_PROVIDER=offline."
    )
