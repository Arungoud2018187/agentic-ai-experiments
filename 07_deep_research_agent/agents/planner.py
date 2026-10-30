"""Planner agent.

Decomposes a research question into answerable sub-questions.  The
planner uses domain concepts detected in the query so the demo produces
focused searches; unknown queries fall back to a generic research plan.
"""

import re

_CONCEPTS = [
    ("agentic ai", "agentic AI"),
    ("agentic", "agentic AI"),
    ("prompt injection", "prompt injection"),
    ("injection", "prompt injection"),
    ("soc", "SOC operations"),
    ("security operations", "SOC operations"),
    ("triage", "alert triage"),
    ("rag", "retrieval augmented generation"),
    ("retrieval", "retrieval augmented generation"),
    ("tool use", "tool use"),
    ("tools", "tool use"),
    ("mcp", "the Model Context Protocol"),
    ("governance", "AI governance"),
    ("compliance", "AI governance"),
    ("evaluation", "LLM evaluation"),
    ("benchmark", "LLM evaluation"),
]


class PlannerAgent:
    name = "PlannerAgent"

    def _concepts(self, query):
        lowered = query.lower()
        found = []
        for keyword, label in _CONCEPTS:
            if keyword in lowered and label not in found:
                found.append(label)
        return found

    def plan(self, query):
        concepts = self._concepts(query)
        lowered = query.lower()

        if "agentic AI" in concepts and "SOC operations" in concepts:
            subquestions = [
                "What is agentic AI and how is it applied to SOC operations?",
                "How does agentic AI improve alert triage and incident response?",
                "What are the main prompt injection and tool-use risks?",
                "Which controls and best practices make agentic deployment safe?",
            ]
        elif "prompt injection" in concepts and "agentic AI" in concepts:
            subquestions = [
                "What is prompt injection in tool-using AI agents?",
                "How can indirect prompt injection enter an agent workflow?",
                "What impact can a successful injection have?",
                "Which defences reduce prompt injection risk?",
            ]
        elif concepts:
            topic = " and ".join(concepts[:2])
            subquestions = [
                f"What is {topic} and why does it matter?",
                f"How does {topic} work in practice?",
                f"What are the risks or limitations of {topic}?",
                f"Which controls or best practices support {topic}?",
            ]
        else:
            topic = re.sub(
                r"^(how|what|why|when|where|which|who)\b\s*",
                "",
                lowered,
            ).strip(" ?.")
            topic = topic or query
            subquestions = [
                f"What is {topic}?",
                f"How does {topic} work?",
                f"What are the risks or limitations of {topic}?",
                f"What are best practices for {topic}?",
            ]

        return {
            "query": query,
            "concepts": concepts,
            "subquestions": subquestions,
            "strategy": "concept-guided decomposition",
        }

    def follow_up_plan(self, gaps):
        return [
            f"Find concrete evidence about: {gap}" for gap in gaps
        ]
