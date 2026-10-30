"""Structured chain-of-thought strategy.

The model is instructed to decompose the problem and show its work
before the final answer.  The offline solver supports every benchmark
category and returns its reasoning trace.
"""

from strategies.llm import ask_llm, first_line
from strategies.solver import solve_by_category

STRUCTURED_PROMPT = """Solve the problem step by step.

1. Identify the known values.
2. Choose the relevant rule or formula.
3. Compute the result.
4. State the final answer on the last line as: ANSWER: <value>

Question: {question}

Reasoning:"""


class StructuredStrategy:
    name = "structured"
    description = "Step-by-step reasoning across all categories"

    def build_prompt(self, question):
        return STRUCTURED_PROMPT.format(question=question)

    def run(self, item):
        prompt = self.build_prompt(item["question"])
        model_answer = ask_llm(prompt)

        if model_answer:
            answer = model_answer
            if "ANSWER:" in model_answer.upper():
                answer = model_answer.upper().split("ANSWER:")[-1].strip().splitlines()[0]
            else:
                answer = first_line(model_answer)
            return {
                "predicted": answer,
                "steps": ["LLM structured reasoning"],
                "mode": "llm",
                "prompt_chars": len(prompt),
            }

        result = solve_by_category(item["question"], item["category"])
        return {
            "predicted": result["answer"],
            "steps": result["steps"],
            "mode": "offline",
            "prompt_chars": len(prompt),
        }
