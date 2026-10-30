# Fine-Tuning for Domain Adaptation - Results

## Dataset
- Generic pretraining rows: 250
- Domain training rows: 250
- Validation rows: 80
- Labels: benign, ddos, insider, malware, phishing

## Model
- Architecture: 256 -> 64 -> 5
- Trainable parameters: 16,773

## Results
| Model | Accuracy | Macro F1 |
|-------|----------|----------|
| pretrained | 48.8% | 0.461 |
| fine_tuned | 100.0% | 1.000 |

Fine-tuning improved validation accuracy by **+51.2 percentage points**.

## Per-class metrics (fine-tuned)

| Class | Precision | Recall | F1 | Support |
|-------|-----------|--------|----|---------|
| benign | 1.000 | 1.000 | 1.000 | 16 |
| ddos | 1.000 | 1.000 | 1.000 | 16 |
| insider | 1.000 | 1.000 | 1.000 | 16 |
| malware | 1.000 | 1.000 | 1.000 | 16 |
| phishing | 1.000 | 1.000 | 1.000 | 16 |

## Confusion matrix (fine-tuned)

Rows = actual, columns = predicted.

| actual \ predicted | benign | ddos | insider | malware | phishing |
|---|---|---|---|---|---|
| benign | 16 | 0 | 0 | 0 | 0 |
| ddos | 0 | 16 | 0 | 0 | 0 |
| insider | 0 | 0 | 16 | 0 | 0 |
| malware | 0 | 0 | 0 | 16 | 0 |
| phishing | 0 | 0 | 0 | 0 | 16 |