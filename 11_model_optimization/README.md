# Experiment 11 - Model Optimization

Compare a FP32 baseline classifier with **INT8 post-training quantization** and
**structured pruning**, measuring accuracy, macro-F1, latency, throughput and
artifact size. The model is a small NumPy MLP so the full benchmark runs on CPU
in under a second and needs no GPU or model server.

## What it demonstrates

- A reproducible support-ticket intent classifier (6 classes) trained from
  scratch with hashed text features and Adam.
- Symmetric per-tensor INT8 quantization of weights with float32 biases.
- Structured pruning of the least important hidden units, which shrinks both
  weight matrices and reduces inference work.
- A combined "prune + quantize" variant and a side-by-side comparison report.

## Layout

```
11_model_optimization/
├── main.py                    # training + benchmark CLI
├── src/
│   ├── baseline.py            # dataset, hashing vectorizer, NumPy MLP
│   ├── quantization.py        # INT8 quantizer, pruning, size estimates
│   ├── benchmark.py           # accuracy/F1, latency, throughput
│   └── comparison.py          # variant runner + report writer
└── results/
    ├── benchmark_results.json
    └── model_optimization_report.md
```

## Run

From this directory:

```bash
python main.py
python main.py --epochs 40 --sparsity 0.6 --runs 200
```

Only `numpy` is required. The default run takes well under a second.

## Captured results

Default configuration: 120 samples/class, 30 epochs, 50% structured pruning,
100 latency runs, seed 42.

| Variant | Accuracy | Macro-F1 | p50 latency | Artifact | Compression |
| --- | ---: | ---: | ---: | ---: | ---: |
| Baseline FP32 | 100.0% | 1.000 | 0.018 ms | 195.5 KB | 1.00x |
| INT8 quantized | 100.0% | 1.000 | 0.020 ms | 49.3 KB | 3.97x |
| Structured prune 50% | 100.0% | 1.000 | 0.016 ms | 97.8 KB | 2.00x |
| Structured prune 50% + INT8 | 100.0% | 1.000 | 0.016 ms | 24.7 KB | 7.93x |

The synthetic task is linearly separable, so all variants retain 100% test
accuracy. The quantization reconstruction error and per-class F1 are recorded in
`results/benchmark_results.json` to show the approximation cost directly.

## Notes

- INT8 weights are dequantized at load time in this NumPy simulation, so the
  measured latency reflects FP32 arithmetic. The main benefit measured here is
  artifact size and memory bandwidth; production speedups require INT8 kernels
  (ONNX Runtime, PyTorch `quantize_dynamic`, etc.).
- Structured pruning is measured with dense arrays, so its latency gain comes
  from the smaller hidden dimension, not from sparse kernels.
- Validate pruning on a larger held-out set before using it in production.
