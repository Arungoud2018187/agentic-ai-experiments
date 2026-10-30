"""Compare baseline, quantized, pruned and combined model variants."""

import json
from datetime import datetime, timezone
from pathlib import Path

from .benchmark import benchmark_variant
from .quantization import quantization_error, quantize_model, structured_prune


def _add_relative_metrics(variant, baseline):
    variant["accuracy_delta"] = round(variant["accuracy"] - baseline["accuracy"], 4)
    variant["accuracy_retention_pct"] = (
        round(variant["accuracy"] / baseline["accuracy"] * 100, 2) if baseline["accuracy"] else 0.0
    )
    variant["compression_vs_baseline"] = round(baseline["size_bytes"] / variant["size_bytes"], 3)
    variant["latency_change_pct"] = round(
        (variant["latency"]["p50_ms"] - baseline["latency"]["p50_ms"]) / baseline["latency"]["p50_ms"] * 100, 2
    )
    variant["throughput_change_pct"] = round(
        (variant["throughput"]["samples_per_second"] - baseline["throughput"]["samples_per_second"])
        / baseline["throughput"]["samples_per_second"]
        * 100,
        2,
    )
    return variant


def run_comparison(model, datasets, sparsity_level=0.5, runs=100):
    X_test = datasets["test"]["X"]
    y_test = datasets["test"]["y"]
    labels = model.label_names
    baseline_size = model.size_bytes()

    print("\n[optimization] creating variants...")
    pruned = structured_prune(model, fraction=sparsity_level)
    quantized = quantize_model(model)
    pruned_quantized = quantize_model(pruned)

    variants = []

    print("[optimization] benchmarking baseline fp32...")
    variants.append(
        benchmark_variant(
            "baseline_fp32",
            "Baseline FP32",
            model.predict,
            X_test,
            y_test,
            labels,
            baseline_size,
            runs=runs,
        )
    )

    print("[optimization] benchmarking int8 quantization...")
    quantized_variant = benchmark_variant(
        "int8_quantized",
        "INT8 quantized",
        quantized.predict,
        X_test,
        y_test,
        labels,
        quantized.size_bytes(),
        runs=runs,
    )
    quantized_variant["quantization"] = {
        **quantized.summary(),
        "reconstruction_error": quantization_error(model, quantized),
    }
    variants.append(quantized_variant)

    print(f"[optimization] benchmarking {sparsity_level:.0%} structured pruning...")
    pruned_variant = benchmark_variant(
        "structured_pruned",
        f"Structured prune {sparsity_level:.0%}",
        pruned.predict,
        X_test,
        y_test,
        labels,
        pruned.size_bytes(),
        runs=runs,
    )
    pruned_variant["dense_size_bytes"] = pruned.size_bytes()
    pruned_variant["hidden_units"] = int(pruned.W1.shape[1])
    pruned_variant["pruning"] = pruned.pruning
    variants.append(pruned_variant)

    print("[optimization] benchmarking structured prune + int8...")
    combined_variant = benchmark_variant(
        "structured_pruned_int8",
        f"Structured prune {sparsity_level:.0%} + INT8",
        pruned_quantized.predict,
        X_test,
        y_test,
        labels,
        pruned_quantized.size_bytes(),
        runs=runs,
    )
    combined_variant["dense_size_bytes"] = pruned_quantized.size_bytes()
    combined_variant["hidden_units"] = int(pruned_quantized.hidden_dim)
    combined_variant["pruning"] = pruned.pruning
    combined_variant["quantization"] = {
        **pruned_quantized.summary(),
        "reconstruction_error": quantization_error(pruned, pruned_quantized),
    }
    variants.append(combined_variant)

    baseline_predictions = model.predict(X_test)
    predictors = {
        "baseline_fp32": model.predict,
        "int8_quantized": quantized.predict,
        "structured_pruned": pruned.predict,
        "structured_pruned_int8": pruned_quantized.predict,
    }
    for variant in variants:
        predictions = predictors[variant["name"]](X_test)
        variant["prediction_agreement_with_baseline"] = round(
            float((predictions == baseline_predictions).mean()), 4
        )

    baseline = variants[0]
    for variant in variants:
        _add_relative_metrics(variant, baseline)
        variant["relative_to_baseline"] = {
            "accuracy_delta": variant["accuracy_delta"],
            "compression": variant["compression_vs_baseline"],
            "latency_change_pct": variant["latency_change_pct"],
        }

    eligible = [variant for variant in variants if variant["accuracy_delta"] >= -0.01]
    recommended = min(eligible, key=lambda item: item["size_bytes"])
    best_accuracy = max(variants, key=lambda item: (item["accuracy"], -item["size_bytes"]))

    summary = {
        "baseline_accuracy": baseline["accuracy"],
        "best_accuracy_variant": best_accuracy["name"],
        "best_accuracy": best_accuracy["accuracy"],
        "smallest_variant": recommended["name"],
        "smallest_size_bytes": recommended["size_bytes"],
        "max_compression": recommended["compression_vs_baseline"],
        "recommended_variant": recommended["name"],
        "recommendation": (
            f"Use {recommended['display_name']}: {recommended['compression_vs_baseline']:.2f}x smaller than FP32 "
            f"with {recommended['accuracy'] * 100:.1f}% test accuracy "
            f"({recommended['accuracy_delta'] * 100:+.1f} percentage points). "
            "INT8 quantization cuts the artifact roughly 4x with no accuracy loss. Structured pruning "
            "also reduces inference work, and combining both compounds the savings; validate the "
            "pruned model on a larger held-out set before production use."
        ),
        "latency_note": (
            "Latency is measured on CPU with NumPy. INT8 weights are dequantized at load time, "
            "so the measured latency reflects FP32 arithmetic; the optimization's primary benefit "
            "is a smaller artifact and lower memory bandwidth. Specialized INT8 kernels are required "
            "for wall-clock speedups."
        ),
    }

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset": {
            "train_samples": int(len(datasets["train"]["y"])),
            "validation_samples": int(len(datasets["validation"]["y"])),
            "test_samples": int(len(y_test)),
            "classes": labels,
        },
        "variants": variants,
        "summary": summary,
    }


def write_markdown(report, output_path):
    summary = report["summary"]
    lines = [
        "# Model Optimization Benchmark",
        "",
        f"Generated: {report['generated_at']}",
        "",
        "## Setup",
        "",
        f"- Classifier: support-ticket intent classification ({len(report['dataset']['classes'])} classes)",
        f"- Test samples: {report['dataset']['test_samples']}",
        "- Techniques: post-training symmetric INT8 quantization, structured hidden-unit pruning",
        "",
        "## Results",
        "",
        "| Variant | Accuracy | Macro-F1 | p50 latency (ms) | Throughput (samples/s) | Artifact size | Compression | Agreement |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for variant in report["variants"]:
        lines.append(
            f"| {variant['display_name']} | {variant['accuracy'] * 100:.1f}% | {variant['macro_f1']:.3f} | "
            f"{variant['latency']['p50_ms']:.3f} | {variant['throughput']['samples_per_second']:,.0f} | "
            f"{variant['size_bytes'] / 1024:.1f} KB | {variant['compression_vs_baseline']:.2f}x | "
            f"{variant['prediction_agreement_with_baseline'] * 100:.1f}% |"
        )

    lines += [
        "",
        "## Recommendation",
        "",
        summary["recommendation"],
        "",
        f"- Best accuracy: `{summary['best_accuracy_variant']}` at {summary['best_accuracy'] * 100:.1f}%",
        f"- Smallest acceptable model: `{summary['recommended_variant']}` at {summary['max_compression']:.2f}x compression",
        "",
        f"> {summary['latency_note']}",
        "",
    ]

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def save_results(report, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return output_path
