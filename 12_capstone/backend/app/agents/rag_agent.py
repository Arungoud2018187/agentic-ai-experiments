"""RAG agent: retrieves grounded answers from the NovaDesk knowledge base."""

import time

from app.tools.retrieval import knowledge_base


class RAGAgent:
    name = "rag"
    description = "Answers policy, pricing, security and product questions with cited knowledge-base context."

    def run(self, question):
        started = time.perf_counter()
        result = knowledge_base.answer(question, top_k=3)
        duration = round((time.perf_counter() - started) * 1000, 2)

        tool_call = {
            "agent": self.name,
            "tool": "knowledge.search",
            "input": question,
            "output": f"{len(result['chunks'])} chunks retrieved",
            "status": "success" if result["chunks"] else "empty",
            "latency_ms": duration,
        }

        return {
            "agent": self.name,
            "answer": result["answer"],
            "confidence": result["confidence"],
            "sources": result["sources"],
            "data": {"chunks": result["chunks"]},
            "tool_calls": [tool_call],
            "latency_ms": duration,
        }
