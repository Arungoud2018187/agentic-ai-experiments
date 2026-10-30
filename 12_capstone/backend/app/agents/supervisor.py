"""Supervisor agent: routes, orchestrates and synthesizes multi-agent answers."""

import time
import uuid
from datetime import datetime, timezone

from app.agents.rag_agent import RAGAgent
from app.agents.research_agent import ResearchAgent
from app.agents.sql_agent import SQLAgent
from app.models.llm import llm_client

ROUTE_TERMS = {
    "sql": {
        "revenue": 3,
        "sales": 3,
        "order": 2,
        "orders": 2,
        "database": 3,
        "customer": 1,
        "customers": 1,
        "how many": 2,
        "average order": 3,
        "ticket": 2,
        "tickets": 2,
        "price": 2,
        "cost": 1,
        "units": 1,
        "products": 2,
        "sell": 2,
        "country": 1,
        "refunded": 3,
    },
    "rag": {
        "policy": 3,
        "pricing": 3,
        "plan": 2,
        "security": 3,
        "compliance": 3,
        "soc 2": 3,
        "gdpr": 3,
        "integration": 2,
        "sla": 3,
        "support hours": 3,
        "refund": 2,
        "onboarding": 2,
        "backup": 2,
        "residency": 3,
        "feature": 2,
        "documentation": 2,
        "what is": 1,
        "how does": 1,
        "company": 2,
        "founded": 2,
        "headquarters": 2,
        "ai assistant": 2,
    },
    "research": {
        "latest": 3,
        "trend": 3,
        "trends": 3,
        "market": 3,
        "research": 3,
        "compare": 2,
        "comparison": 2,
        "competitor": 3,
        "industry": 3,
        "best practice": 2,
        "benchmark": 2,
        "forecast": 2,
        "web": 2,
        "2026": 1,
    },
}

AGENT_LABELS = {
    "sql": "Operational data",
    "rag": "Knowledge base",
    "research": "Research",
}


class Supervisor:
    def __init__(self):
        self.agents = {
            "sql": SQLAgent(),
            "rag": RAGAgent(),
            "research": ResearchAgent(),
        }

    def score(self, question):
        text = question.lower()
        return {
            name: sum(weight for phrase, weight in terms.items() if phrase in text)
            for name, terms in ROUTE_TERMS.items()
        }

    def plan(self, question):
        scores = self.score(question)
        primary = max(scores, key=lambda name: scores[name])
        if scores[primary] <= 0:
            primary = "rag"

        secondary = None
        remaining = [name for name in ("sql", "rag", "research") if name != primary]
        candidate = max(remaining, key=lambda name: scores[name])
        multi_signal = " and " in question.lower() or question.count("?") > 1 or ";" in question
        if multi_signal and scores[candidate] >= 3:
            secondary = candidate

        agents = [primary] + ([secondary] if secondary else [])
        reason = f"Matched {primary} signals ({scores[primary]} points)"
        if secondary:
            reason += f" and combined with {secondary} ({scores[secondary]} points)"

        confidence = min(0.97, 0.5 + scores[primary] * 0.045)
        return {
            "primary": primary,
            "agents": agents,
            "scores": scores,
            "reason": reason,
            "confidence": round(confidence, 3),
        }

    def handle(self, question):
        question = (question or "").strip()
        if not question:
            raise ValueError("Question must not be empty")

        started = time.perf_counter()
        routing = self.plan(question)
        results = []
        tool_calls = []

        for name in routing["agents"]:
            try:
                result = self.agents[name].run(question)
            except Exception as exc:  # noqa: BLE001 - one agent must not sink the request
                result = {
                    "agent": name,
                    "answer": f"The {name} agent failed: {exc}",
                    "confidence": 0.0,
                    "sources": [],
                    "data": {"error": str(exc)},
                    "tool_calls": [
                        {
                            "agent": name,
                            "tool": f"{name}.run",
                            "input": question,
                            "output": str(exc),
                            "status": "error",
                            "latency_ms": 0,
                        }
                    ],
                    "latency_ms": 0,
                }
            results.append(result)
            tool_calls.extend(result.get("tool_calls", []))

        if len(results) == 1:
            fallback_answer = results[0]["answer"]
        else:
            parts = []
            for result in results:
                parts.append(f"{AGENT_LABELS.get(result['agent'], result['agent'])}:\n{result['answer']}")
            fallback_answer = "\n\n".join(parts)

        context_parts = []
        for result in results:
            context_parts.append(f"[{result['agent']}] {result['answer']}")
            titles = [source.get("title", "") for source in result.get("sources", [])]
            if titles:
                context_parts.append("Sources: " + "; ".join(titles))
        llm_result = llm_client.synthesize(question, "\n".join(context_parts), fallback=fallback_answer)

        sources = []
        seen_sources = set()
        for result in results:
            for source in result.get("sources", []):
                key = (source.get("type"), source.get("id") or source.get("url") or source.get("title"))
                if key in seen_sources:
                    continue
                seen_sources.add(key)
                sources.append(source)

        data = {result["agent"]: result.get("data", {}) for result in results}
        confidence = round(sum(result["confidence"] for result in results) / len(results), 3)
        latency = round((time.perf_counter() - started) * 1000, 2)

        return {
            "id": str(uuid.uuid4()),
            "question": question,
            "answer": llm_result.text,
            "agents": [result["agent"] for result in results],
            "routing": routing,
            "confidence": confidence,
            "sources": sources,
            "tool_calls": tool_calls,
            "data": data,
            "provider": llm_result.provider,
            "model": llm_result.model,
            "llm": llm_result.to_dict(),
            "latency_ms": latency,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def describe_agents(self):
        return [
            {
                "name": agent.name,
                "description": agent.description,
                "status": "ready",
                "tools": [
                    "sql.query" if agent.name == "sql"
                    else "knowledge.search" if agent.name == "rag"
                    else "web.search, knowledge.search"
                ],
            }
            for agent in self.agents.values()
        ]


supervisor = Supervisor()
