"""Latency, throughput, accuracy and model-size measurement utilities."""

import math
import time

import numpy as np


def classification_metrics(y_true, y_pred, labels):
    labels = list(labels)
    matrix = np.zeros((len(labels), len(labels)), dtype=np.int64)
    for truth, prediction in zip(y_true, y_pred):
        matrix[int(truth), int(prediction)] += 1

    per_class = []
    for index, label in enumerate(labels):
        true_positive = int(matrix[index, index])
        false_positive = int(matrix[:, index].sum() - true_positive)
        false_negative = int(matrix[index, :].sum() - true_positive)
        precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
        recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class.append(
            {
                "label": label,
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1": round(f1, 4),
                "support": int(matrix[index, :].sum()),
            }
        )

    accuracy = float(np.trace(matrix) / matrix.sum()) if matrix.sum() else 0.0
    macro_f1 = float(np.mean([item["f1"] for item in per_class])) if per_class else 0.0
    return {
        "accuracy": round(accuracy, 4),
        "macro_f1": round(macro_f1, 4),
        "per_class": per_class,
        "confusion_matrix": matrix.tolist(),
    }


def measure_latency(predict, sample, runs=100, warmup=10, inner_repeats=10):
    """Measure single-sample inference latency in milliseconds.

    Each timing loops over ``inner_repeats`` forwards and divides by the
    count so microsecond-scale inference is not dominated by timer overhead.
    """
    sample = np.asarray(sample, dtype=np.float32).reshape(1, -1)
    for _ in range(warmup):
        predict(sample)

    timings = []
    for _ in range(runs):
        start = time.perf_counter_ns()
        for _ in range(inner_repeats):
            predict(sample)
        elapsed_ms = (time.perf_counter_ns() - start) / 1_000_000 / inner_repeats
        timings.append(elapsed_ms)

    timings.sort()
    count = len(timings)
    p50 = timings[count // 2]
    p95 = timings[min(count - 1, int(math.ceil(0.95 * count)) - 1)]
    return {
        "runs": runs,
        "inner_repeats": inner_repeats,
        "mean_ms": round(float(np.mean(timings)), 4),
        "p50_ms": round(p50, 4),
        "p95_ms": round(p95, 4),
        "min_ms": round(float(timings[0]), 4),
        "max_ms": round(float(timings[-1]), 4),
        "throughput_per_second": round(1000.0 / p50, 1) if p50 > 0 else None,
    }


def measure_throughput(predict, batch, repeats=30, warmup=3):
    """Measure batched inference throughput (samples/second)."""
    batch = np.asarray(batch, dtype=np.float32)
    for _ in range(warmup):
        predict(batch)

    start = time.perf_counter()
    for _ in range(repeats):
        predict(batch)
    elapsed = time.perf_counter() - start
    return {
        "batch_size": int(len(batch)),
        "repeats": repeats,
        "samples_per_second": round(len(batch) * repeats / elapsed, 1),
    }


def benchmark_variant(name, display_name, predict, X_test, y_test, labels, size_bytes, runs=100, batch=None):
    predictions = predict(X_test)
    metrics = classification_metrics(y_test, predictions, labels)
    latency = measure_latency(predict, X_test[0], runs=runs)
    throughput = measure_throughput(predict, batch if batch is not None else X_test[:64])

    return {
        "name": name,
        "display_name": display_name,
        "accuracy": metrics["accuracy"],
        "macro_f1": metrics["macro_f1"],
        "per_class": metrics["per_class"],
        "confusion_matrix": metrics["confusion_matrix"],
        "test_samples": int(len(y_test)),
        "latency": latency,
        "throughput": throughput,
        "size_bytes": int(size_bytes),
        "size_mb": round(size_bytes / (1024 * 1024), 4),
    }
