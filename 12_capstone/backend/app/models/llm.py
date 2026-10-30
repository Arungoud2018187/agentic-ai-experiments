"""LLM client with Ollama, OpenAI-compatible and deterministic offline modes.

The capstone is fully functional without a model server: every agent
builds a grounded answer from its tool output and the LLM is only used
to polish that answer when a provider is configured.
"""

import time
from dataclasses import asdict, dataclass

import requests

from app.config import settings


@dataclass
class LLMResult:
    text: str
    provider: str
    model: str
    latency_ms: float
    fallback: bool = False
    error: str | None = None

    def to_dict(self):
        return asdict(self)


class LLMClient:
    def __init__(self, provider=None, timeout=None):
        self.configured_provider = (provider or settings.llm_provider or "offline").lower()
        self.timeout = timeout or settings.llm_timeout_seconds
        self._auto_provider = None

    def _resolve_provider(self):
        if self.configured_provider != "auto":
            return self.configured_provider
        if self._auto_provider:
            return self._auto_provider

        try:
            response = requests.get(f"{settings.ollama_base_url}/api/tags", timeout=1.5)
            if response.ok:
                self._auto_provider = "ollama"
                return self._auto_provider
        except requests.RequestException:
            pass

        if settings.openai_api_key:
            self._auto_provider = "openai"
            return self._auto_provider

        self._auto_provider = "offline"
        return self._auto_provider

    def generate(self, prompt, system=None, fallback="", temperature=0.1, max_tokens=500):
        provider = self._resolve_provider()
        started = time.perf_counter()

        if provider == "offline":
            return LLMResult(
                text=fallback,
                provider="offline",
                model="deterministic-rules",
                latency_ms=round((time.perf_counter() - started) * 1000, 2),
                fallback=True,
            )

        try:
            if provider == "ollama":
                text = self._generate_ollama(prompt, system, temperature, max_tokens)
                model = settings.ollama_model
            elif provider == "openai":
                text = self._generate_openai(prompt, system, temperature, max_tokens)
                model = settings.openai_model
            else:
                raise ValueError(f"Unsupported LLM provider: {provider}")

            if not text.strip():
                raise ValueError("Provider returned an empty response")
            return LLMResult(
                text=text.strip(),
                provider=provider,
                model=model,
                latency_ms=round((time.perf_counter() - started) * 1000, 2),
            )
        except Exception as exc:  # noqa: BLE001 - provider failures must not break the API
            return LLMResult(
                text=fallback,
                provider=provider,
                model=self._model_for(provider),
                latency_ms=round((time.perf_counter() - started) * 1000, 2),
                fallback=True,
                error=str(exc)[:300],
            )

    def synthesize(self, question, context, fallback):
        system = (
            "You are the synthesis layer of a multi-agent assistant. Answer using only the "
            "supplied tool context. Be concise, keep numbers exact, and mention source titles. "
            "If the context is insufficient, say so instead of inventing facts."
        )
        prompt = f"Question: {question}\n\nTool context:\n{context}\n\nWrite the final answer."
        return self.generate(prompt, system=system, fallback=fallback, temperature=0.1, max_tokens=450)

    def status(self):
        provider = self._resolve_provider()
        return {
            "configured_provider": self.configured_provider,
            "active_provider": provider,
            "model": self._model_for(provider),
            "fallback_mode": provider == "offline",
        }

    def _model_for(self, provider):
        if provider == "ollama":
            return settings.ollama_model
        if provider == "openai":
            return settings.openai_model
        return "deterministic-rules"

    def _generate_ollama(self, prompt, system, temperature, max_tokens):
        payload = {
            "model": settings.ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        if system:
            payload["system"] = system
        response = requests.post(
            f"{settings.ollama_base_url}/api/generate",
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json().get("response", "")

    def _generate_openai(self, prompt, system, temperature, max_tokens):
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not configured")
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        response = requests.post(
            f"{settings.openai_base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.openai_model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]


llm_client = LLMClient()
