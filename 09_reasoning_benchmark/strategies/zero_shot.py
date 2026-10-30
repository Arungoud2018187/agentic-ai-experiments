"""Zero-shot prompting strategy.

The model is asked for a direct answer.  In offline mode only simple
arithmetic and percentage questions are supported by the fallback
solver, which is representative of a model that has not been given
worked examples or a reasoning scaffold.
"""

from strategies.llm import ask_llm, first_line
from strategies.solver import solve_by_category

SUPPORTED = {"arithmetic", "percentage"}


class ZeroShotStrategy:
    name = "zero_shot"
    description = "Direct answer, no examples or reasoning scaffold"

    def build_prompt(self, question):
        return (
            "Answer the following question. Return only the final answer.\n\n"
            f"Question: {question}\nAnswer:"
        )

    def run(self, item):
        prompt = self.build_prompt(item["question"])
        model_answer = first_line(ask_llm(prompt))

        if model_answer:
            return {
                "predicted": model_answer,
                "steps": ["LLM direct answer"],
                "mode": "llm",
                "prompt_chars": len(prompt),
            }

        if item["category"] not in SUPPORTED:
            return {
                "predicted": "unknown",
                "steps": [f"Zero-shot fallback does not cover '{item['category']}'"],
                "mode": "offline",
                "prompt_chars": len(prompt),
            }

        result = solve_by_category(item["question"], item["category"])
        return {
            "predicted": result["answer"],
            "steps": result["steps"][-1:],
            "mode": "offline",
            "prompt_chars": len(prompt),
        }
