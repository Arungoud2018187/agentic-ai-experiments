"""Few-shot prompting strategy.

Worked examples improve format adherence and let the offline solver
cover algebraic, average and probability questions in addition to the
zero-shot arithmetic/percentage set.
"""

from strategies.llm import ask_llm, first_line
from strategies.solver import solve_by_category

SUPPORTED = {"arithmetic", "percentage", "algebra", "average", "probability"}

EXAMPLES = [
    {
        "question": "What is 12 + 8?",
        "answer": "20",
    },
    {
        "question": "What is 15% of 200?",
        "answer": "30",
    },
    {
        "question": "Solve for x: 2x + 3 = 11",
        "answer": "4",
    },
]

FEW_SHOT_PROMPT = """Answer the questions using the worked examples.

{examples}

Question: {question}
Answer:"""


class FewShotStrategy:
    name = "few_shot"
    description = "Three worked examples followed by the question"

    def build_prompt(self, question):
        examples = "\n\n".join(
            f"Question: {example['question']}\nAnswer: {example['answer']}"
            for example in EXAMPLES
        )
        return FEW_SHOT_PROMPT.format(examples=examples, question=question)

    def run(self, item):
        prompt = self.build_prompt(item["question"])
        model_answer = first_line(ask_llm(prompt))

        if model_answer:
            return {
                "predicted": model_answer,
                "steps": ["LLM few-shot answer"],
                "mode": "llm",
                "prompt_chars": len(prompt),
            }

        if item["category"] not in SUPPORTED:
            return {
                "predicted": "unknown",
                "steps": [f"Few-shot fallback does not cover '{item['category']}'"],
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
