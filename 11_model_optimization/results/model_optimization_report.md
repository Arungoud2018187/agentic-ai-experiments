# Model Optimization Benchmark

Generated: 2026-10-30T10:10:45.223889+00:00

## Setup

- Classifier: support-ticket intent classification (6 classes)
- Test samples: 109
- Techniques: post-training symmetric INT8 quantization, structured hidden-unit pruning

## Results

| Variant | Accuracy | Macro-F1 | p50 latency (ms) | Throughput (samples/s) | Artifact size | Compression | Agreement |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline FP32 | 100.0% | 1.000 | 0.018 | 253,238 | 195.5 KB | 1.00x | 100.0% |
| INT8 quantized | 100.0% | 1.000 | 0.019 | 314,193 | 49.3 KB | 3.97x | 100.0% |
| Structured prune 50% | 100.0% | 1.000 | 0.018 | 506,423 | 97.8 KB | 2.00x | 100.0% |
| Structured prune 50% + INT8 | 100.0% | 1.000 | 0.018 | 554,513 | 24.7 KB | 7.93x | 100.0% |

## Recommendation

Use Structured prune 50% + INT8: 7.93x smaller than FP32 with 100.0% test accuracy (+0.0 percentage points). INT8 quantization cuts the artifact roughly 4x with no accuracy loss. Structured pruning also reduces inference work, and combining both compounds the savings; validate the pruned model on a larger held-out set before production use.

- Best accuracy: `structured_pruned_int8` at 100.0%
- Smallest acceptable model: `structured_pruned_int8` at 7.93x compression

> Latency is measured on CPU with NumPy. INT8 weights are dequantized at load time, so the measured latency reflects FP32 arithmetic; the optimization's primary benefit is a smaller artifact and lower memory bandwidth. Specialized INT8 kernels are required for wall-clock speedups.
