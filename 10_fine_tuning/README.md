# Experiment 10 - Fine-Tuning for Domain Adaptation

## Aim
Adapt a small neural classifier from a generic incident corpus to a
security-domain incident corpus, then measure the improvement on a
held-out validation set.

## Approach
1. **Prepare data** - generate a balanced generic corpus and a
   domain-specific corpus of incident descriptions across five labels:
   `benign`, `ddos`, `insider`, `malware`, `phishing`.
2. **Pretrain** a NumPy MLP (256 hashed features -> 64 ReLU -> 5 softmax)
   on the generic corpus.
3. **Fine-tune** the same weights on the domain corpus with a lower
   learning rate.
4. **Evaluate** both checkpoints on the domain validation set with
   accuracy, macro F1, per-class metrics and a confusion matrix.

This mirrors the pretrain -> fine-tune workflow used with large language
models, at a scale that runs on a CPU in seconds.

## Files
| File | Purpose |
|------|---------|
| `scripts/prepare_dataset.py` | Generates `train.jsonl`, `validation.jsonl`, `generic_train.jsonl` |
| `scripts/mlp.py` | Hashing vectorizer, MLP, Adam optimiser, save/load |
| `scripts/train.py` | Pretraining + domain fine-tuning |
| `scripts/evaluate.py` | Metrics and reports |

## Run
```bash
python scripts/prepare_dataset.py --force
python scripts/train.py
python scripts/evaluate.py
```

## Results (current run)
| Model | Accuracy | Macro F1 |
|-------|----------|----------|
| Pretrained on generic corpus | 48.8% | 0.461 |
| Fine-tuned on domain corpus | 100.0% | 1.000 |

Domain fine-tuning improved validation accuracy by **+51.2 percentage
points**.  The domain corpus uses specialised indicators (ransomware,
SYN flood, credential harvesting, USB exfiltration, etc.) that are absent
from the generic corpus, which is exactly the gap that domain adaptation
is meant to close.

## Output
- `models/pretrained_model.npz`, `models/finetuned_model.npz`
- `models/training_metadata.json`
- `results/fine_tuning_results.json`
- `results/fine_tuning_report.md`
