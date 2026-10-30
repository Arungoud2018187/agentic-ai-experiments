"""Experiment 9 - Reasoning Model Benchmarking.

Compares three prompting strategies on a 12-question reasoning
benchmark: zero-shot, few-shot and structured chain-of-thought.

Usage:
    python main.py
    python main.py --strategy structured
    USE_LLM=1 python main.py          # use Ollama when available
"""

import argparse
import json
from pathlib import Path

from evaluation.evaluator import evaluate_strategy, load_benchmark
from strategies.few_shot import FewShotStrategy
from strategies.structured import StructuredStrategy
from strategies.zero_shot import ZeroShotStrategy

RESULT_DIR = Path(__file__).resolve().parent / "results"

STRATEGIES = {
    "zero_shot": ZeroShotStrategy,
    "few_shot": FewShotStrategy,
    "structured": StructuredStrategy,
}


def _print_strategy(result):
    print("\n" + "=" * 60)
    print(f"STRATEGY: {result['strategy']} - {result['description']}")
    print("=" * 60)
    print(
        f"Accuracy: {result['accuracy'] * 100:.1f}% "
        f"({result['correct']}/{result['total']}) | "
        f"avg latency: {result['average_latency_ms']:.2f} ms | "
        f"avg prompt: {result['average_prompt_chars']} chars"
    )

    header = f"{'ID':<5}{'Category':<15}{'Expected':<12}{'Predicted':<12}{'OK':<4}"
    print(header)
    print("-" * len(header))
    for record in result["records"]:
        print(
            f"{record['id']:<5}{record['category']:<15}"
            f"{record['expected']:<12}{record['predicted'][:10]:<12}"
            f"{'yes' if record['correct'] else 'NO'}"
        )

    print("\nPer-category accuracy:")
    for category, values in result["by_category"].items():
        print(
            f"  {category:<15} {values['accuracy'] * 100:>6.1f}% "
            f"({values['correct']}/{values['total']})"
        )


def _markdown(results):
    lines = [
        "# Reasoning Benchmark Report",
        "",
        f"Benchmark questions: {results[0]['total'] if results else 0}",
        "",
        "| Strategy | Accuracy | Correct | Avg latency (ms) | Avg prompt (chars) |",
        "|----------|----------|---------|------------------|--------------------|",
    ]
    for result in results:
        lines.append(
            f"| {result['strategy']} | {result['accuracy'] * 100:.1f}% | "
            f"{result['correct']}/{result['total']} | "
            f"{result['average_latency_ms']:.2f} | {result['average_prompt_chars']} |"
        )

    lines += ["", "## Per-category accuracy", ""]
    categories = sorted({key for result in results for key in result["by_category"]})
    header = "| Category | " + " | ".join(result["strategy"] for result in results) + " |"
    lines.append(header)
    lines.append("|----------|" + "|".join("----------" for _ in results) + "|")
    for category in categories:
        cells = []
        for result in results:
            value = result["by_category"].get(category)
            cells.append(f"{value['accuracy'] * 100:.1f}%" if value else "-")
        lines.append(f"| {category} | " + " | ".join(cells) + " |")

    return "\n".join(lines)


def run(selected=None, output_dir=None):
    print("=" * 60)
    print("          REASONING MODEL BENCHMARK")
    print("=" * 60)

    dataset = load_benchmark()
    print(f"\nLoaded {len(dataset)} benchmark questions.")

    names = selected or list(STRATEGIES)
    results = []

    for name in names:
        print(f"\nRunning strategy: {name}")
        result = evaluate_strategy(STRATEGIES[name](), dataset)
        _print_strategy(result)
        results.append(result)

    print("\n" + "=" * 60)
    print("COMPARISON")
    print("=" * 60)
    for result in results:
        print(
            f"{result['strategy']:<12} accuracy={result['accuracy'] * 100:>6.1f}% "
            f"latency={result['average_latency_ms']:>7.2f} ms "
            f"prompt={result['average_prompt_chars']:>4} chars"
        )

    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        payload = {"benchmark_size": len(dataset), "results": results}
        (output_dir / "reasoning_benchmark_results.json").write_text(
            json.dumps(payload, indent=2), encoding="utf-8"
        )
        (output_dir / "reasoning_benchmark_report.md").write_text(
            _markdown(results), encoding="utf-8"
        )
        print(f"\nSaved results to {output_dir}")

    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strategy",
        action="append",
        choices=sorted(STRATEGIES),
        help="strategy to run (repeatable); defaults to all",
    )
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--output-dir", default=str(RESULT_DIR))
    args = parser.parse_args()

    run(args.strategy, output_dir=args.output_dir)


if __name__ == "__main__":
    main()
