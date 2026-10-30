"""Research agent: combines the simulated web index with internal knowledge."""

import time

from app.tools.retrieval import knowledge_base
from app.tools.web_search import web_search


class ResearchAgent:
    name = "research"
    description = "Synthesizes market, competitor and best-practice research from the web index plus internal docs."

    def run(self, question):
        started = time.perf_counter()
        web_results = web_search.search(question, max_results=3)
        internal = knowledge_base.search(question, top_k=2)

        lines = []
        if web_results:
            lines.append("External findings:")
            for index, item in enumerate(web_results, start=1):
                lines.append(f"{index}. {item['title']} — {item['snippet']} ({item['url']})")
        else:
            lines.append("No external results matched the query.")

        if internal:
            lines.append("\nInternal context:")
            for item in internal:
                lines.append(f"- {item['title']}: {item['text'][:260]}")

        answer = "\n".join(lines)
        sources = [
            {
                "type": "web",
                "id": item["id"],
                "title": item["title"],
                "url": item["url"],
                "snippet": item["snippet"],
                "score": item["score"],
            }
            for item in web_results
        ]
        seen_docs = set()
        for item in internal:
            if item["doc_id"] in seen_docs:
                continue
            seen_docs.add(item["doc_id"])
            sources.append(
                {
                    "type": "knowledge_base",
                    "id": item["doc_id"],
                    "title": item["title"],
                    "snippet": item["text"][:180],
                    "score": item["score"],
                }
            )

        duration = round((time.perf_counter() - started) * 1000, 2)
        confidence = 0.82 if web_results else 0.45
        return {
            "agent": self.name,
            "answer": answer,
            "confidence": confidence,
            "sources": sources,
            "data": {
                "web_results": [
                    {
                        "title": item["title"],
                        "url": item["url"],
                        "snippet": item["snippet"],
                        "score": item["score"],
                    }
                    for item in web_results
                ],
                "internal_chunks": [
                    {"title": item["title"], "score": item["score"], "text": item["text"][:300]}
                    for item in internal
                ],
            },
            "tool_calls": [
                {
                    "agent": self.name,
                    "tool": "web.search",
                    "input": question,
                    "output": f"{len(web_results)} results",
                    "status": "success" if web_results else "empty",
                    "latency_ms": round(duration * 0.7, 2),
                },
                {
                    "agent": self.name,
                    "tool": "knowledge.search",
                    "input": question,
                    "output": f"{len(internal)} chunks",
                    "status": "success" if internal else "empty",
                    "latency_ms": round(duration * 0.3, 2),
                },
            ],
            "latency_ms": duration,
        }
