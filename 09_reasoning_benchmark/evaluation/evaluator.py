"""Benchmark evaluator.

Normalises answers (numbers, percentages, yes/no) and reports accuracy,
per-category performance, latency and prompt size for each strategy.
"""

import json
import re
import time
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
BENCHMARK_PATH = BASE_DIR / "data" / "benchmark.json"


def load_benchmark():
    return json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))


def _numeric(value):
    text = str(value).strip().lower().replace(",", "")
    if text.endswith("%"):
        text = text[:-1]
    try:
        return float(text)
    except ValueError:
        return None


def normalize(value):
    text = str(value).strip().lower()
    text = re.sub(r"[.!?]+$", "", text)
    return " ".join(text.split())


def is_correct(predicted, expected):
    predicted_number = _numeric(predicted)
    expected_number = _numeric(expected)

    if predicted_number is not None and expected_number is not None:
        return abs(predicted_number - expected_number) <= 1e-6

    return normalize(predicted) == normalize(expected)


def evaluate_strategy(strategy, dataset=None):
    dataset = dataset or load_benchmark()
    records = []

    for item in dataset:
        started = time.perf_counter()
        output = strategy.run(item)
        latency_ms = (time.perf_counter() - started) * 1000

        correct = is_correct(output["predicted"], item["answer"])
        records.append(
            {
                "id": item["id"],
                "category": item["category"],
                "difficulty": item["difficulty"],
                "question": item["question"],
                "expected": item["answer"],
                "predicted": output["predicted"],
                "correct": correct,
                "steps": output["steps"],
                "mode": output["mode"],
                "latency_ms": round(latency_ms, 2),
                "prompt_chars": output["prompt_chars"],
            }
        )

    total = len(records)
    correct_count = sum(record["correct"] for record in records)

    by_category = defaultdict(lambda: {"correct": 0, "total": 0})
    for record in records:
        by_category[record["category"]]["total"] += 1
        by_category[record["category"]]["correct"] += int(record["correct"])

    category_scores = {
        category: {
            "accuracy": round(values["correct"] / values["total"], 3),
            "correct": values["correct"],
            "total": values["total"],
        }
        for category, values in sorted(by_category.items())
    }

    return {
        "strategy": strategy.name,
        "description": getattr(strategy, "description", ""),
        "accuracy": round(correct_count / total, 3) if total else 0.0,
        "correct": correct_count,
        "total": total,
        "average_latency_ms": round(
            sum(record["latency_ms"] for record in records) / total, 2
        )
        if total
        else 0,
        "average_prompt_chars": round(
            sum(record["prompt_chars"] for record in records) / total
        )
        if total
        else 0,
        "by_category": category_scores,
        "records": records,
    }
