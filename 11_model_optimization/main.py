"""Experiment 11 - Model Optimization.

Train a small NumPy intent classifier, then compare the FP32 baseline
against INT8 quantization, magnitude pruning, and combined compression.

Usage:
    python main.py
    python main.py --epochs 40 --sparsity 0.6 --runs 200
"""

import argparse
import json
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from src.baseline import train_baseline  # noqa: E402
from src.comparison import run_comparison, save_results, write_markdown  # noqa: E402

RESULT_DIR = BASE_DIR / "results"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples-per-class", type=int, default=120)
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--sparsity", type=float, default=0.5)
    parser.add_argument("--runs", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", default=str(RESULT_DIR / "benchmark_results.json"))
    parser.add_argument("--report", default=str(RESULT_DIR / "model_optimization_report.md"))
    args = parser.parse_args()

    started = time.perf_counter()
    print("=" * 72)
    print("              MODEL OPTIMIZATION BENCHMARK")
    print("=" * 72)

    print("\n[1/3] Training the FP32 baseline classifier...")
    model, datasets, metrics = train_baseline(
        samples_per_class=args.samples_per_class,
        epochs=args.epochs,
        seed=args.seed,
    )

    print(f"\nModel: {model.summary()['parameters']:,} parameters, {model.size_bytes() / 1024:.1f} KB")
    for split, values in metrics.items():
        print(f"  {split:<10} accuracy={values['accuracy'] * 100:6.2f}%  ({values['samples']} samples)")

    print("\n[2/3] Applying optimization techniques and benchmarking...")
    report = run_comparison(model, datasets, sparsity_level=args.sparsity, runs=args.runs)

    report["training"] = {
        "samples_per_class": args.samples_per_class,
        "epochs": args.epochs,
        "seed": args.seed,
        "metrics": metrics,
        "model_summary": model.summary(),
    }
    report["configuration"] = {
        "sparsity": args.sparsity,
        "benchmark_runs": args.runs,
        "seed": args.seed,
    }
    report["duration_seconds"] = round(time.perf_counter() - started, 2)

    print("\n[3/3] Comparison")
    print("-" * 72)
    header = f"{'Variant':<34}{'Accuracy':>9}{'p50 ms':>9}{'Size':>11}{'Compress':>10}"
    print(header)
    print("-" * 72)
    for variant in report["variants"]:
        print(
            f"{variant['display_name']:<34}"
            f"{variant['accuracy'] * 100:>8.1f}%"
            f"{variant['latency']['p50_ms']:>9.3f}"
            f"{variant['size_bytes'] / 1024:>9.1f} KB"
            f"{variant['compression_vs_baseline']:>9.2f}x"
        )

    print("\nRecommendation:")
    print(report["summary"]["recommendation"])
    print(f"\nLatency note: {report['summary']['latency_note']}")

    output_path = save_results(report, args.output)
    report_path = write_markdown(report, args.report)

    print(f"\nSaved JSON results to {output_path}")
    print(f"Saved markdown report to {report_path}")
    print(f"Total runtime: {report['duration_seconds']:.2f}s")


if __name__ == "__main__":
    main()
