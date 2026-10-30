"""SQL agent: answers operational questions against the demo SQLite database."""

import time

from app.tools import database


class SQLAgent:
    name = "sql"
    description = "Queries customers, products, orders and support tickets in the demo SQLite database."

    def run(self, question):
        started = time.perf_counter()
        result = database.answer_question(question)
        duration = round((time.perf_counter() - started) * 1000, 2)

        status = "error" if result["error"] else "success"
        confidence = 0.95 if result["intent"] != "overview" and not result["error"] else 0.55
        if result["row_count"] == 0:
            confidence = min(confidence, 0.6)

        tool_call = {
            "agent": self.name,
            "tool": "sql.query",
            "input": result["sql"],
            "output": result["error"] or f"{result['row_count']} rows returned",
            "status": status,
            "latency_ms": duration,
        }

        return {
            "agent": self.name,
            "answer": result["answer"],
            "confidence": confidence,
            "sources": [
                {
                    "type": "database",
                    "id": "demo-db",
                    "title": "NovaDesk demo SQLite database",
                    "snippet": f"Intent: {result['intent']} | SQL: {result['sql'][:220]}",
                }
            ],
            "data": {
                "intent": result["intent"],
                "sql": result["sql"],
                "columns": result["columns"],
                "rows": result["rows"],
                "row_count": result["row_count"],
                "error": result["error"],
            },
            "tool_calls": [tool_call],
            "latency_ms": duration,
        }
