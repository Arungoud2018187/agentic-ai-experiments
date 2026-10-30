# Experiment 9 - Reasoning Model Benchmarking

## Aim
Compare zero-shot, few-shot and structured chain-of-thought prompting on
a reproducible 12-question reasoning benchmark spanning eight categories.

## Benchmark categories
arithmetic, percentage, algebra, logic, sequence, probability, average,
combinatorics.

## Strategies
| Strategy | Coverage in offline mode | Prompt |
|----------|--------------------------|--------|
| `zero_shot` | arithmetic, percentage | direct answer |
| `few_shot` | + algebra, average, probability | three worked examples |
| `structured` | all categories | step-by-step reasoning + final `ANSWER:` |

The strategies share the same deterministic solver (`strategies/solver.py`)
so the comparison isolates the effect of the prompting scaffold.  Set
`USE_LLM=1` with Ollama running to benchmark a real model instead.

## Files
| File | Purpose |
|------|---------|
| `data/benchmark.json` | Questions, categories, answers |
| `strategies/solver.py` | Explainable category solvers |
| `strategies/*.py` | Prompt builders + strategy runners |
| `evaluation/evaluator.py` | Answer normalisation, accuracy, latency |
| `main.py` | Runs strategies and writes the comparison report |

## Run
```bash
python main.py
python main.py --strategy structured
```

## Output
- `results/reasoning_benchmark_results.json`
- `results/reasoning_benchmark_report.md`
