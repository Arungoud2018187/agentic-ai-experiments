"""Evaluate the pretrained and fine-tuned models on the validation set."""

import json
import sys
from pathlib import Path

from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "models"
RESULT_DIR = BASE_DIR / "results"

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mlp import MLP, encode_labels, vectorize_many  # noqa: E402
from prepare_dataset import load_jsonl, prepare  # noqa: E402


def evaluate_model(model, X, y):
    predictions = model.predict(X)
    return {
        "accuracy": round(float(accuracy_score(y, predictions)), 4),
        "macro_f1": round(float(f1_score(y, predictions, average="macro")), 4),
        "per_class": classification_report(
            y,
            predictions,
            labels=list(range(len(model.label_names))),
            target_names=model.label_names,
            output_dict=True,
            zero_division=0,
        ),
        "confusion_matrix": confusion_matrix(
            y, predictions, labels=list(range(len(model.label_names)))
        ).tolist(),
        "predictions": predictions.tolist(),
    }


def _markdown(results, metadata):
    lines = [
        "# Fine-Tuning for Domain Adaptation - Results",
        "",
        "## Dataset",
        f"- Generic pretraining rows: {metadata['generic_rows']}",
        f"- Domain training rows: {metadata['train_rows']}",
        f"- Validation rows: {metadata['validation_rows']}",
        f"- Labels: {', '.join(metadata['labels'])}",
        "",
        "## Model",
        f"- Architecture: {metadata['model_summary']['input_dim']} -> "
        f"{metadata['model_summary']['hidden_dim']} -> "
        f"{metadata['model_summary']['output_dim']}",
        f"- Trainable parameters: {metadata['model_summary']['parameters']:,}",
        "",
        "## Results",
        "| Model | Accuracy | Macro F1 |",
        "|-------|----------|----------|",
    ]
    for name, result in results.items():
        lines.append(
            f"| {name} | {result['accuracy'] * 100:.1f}% | {result['macro_f1']:.3f} |"
        )

    lines += [
        "",
        f"Fine-tuning improved validation accuracy by "
        f"**{metadata['improvement'] * 100:+.1f} percentage points**.",
        "",
        "## Per-class metrics (fine-tuned)",
        "",
        "| Class | Precision | Recall | F1 | Support |",
        "|-------|-----------|--------|----|---------|",
    ]
    for label in metadata["labels"]:
        metrics = results["fine_tuned"]["per_class"][label]
        lines.append(
            f"| {label} | {metrics['precision']:.3f} | {metrics['recall']:.3f} | "
            f"{metrics['f1-score']:.3f} | {int(metrics['support'])} |"
        )

    lines += [
        "",
        "## Confusion matrix (fine-tuned)",
        "",
        "Rows = actual, columns = predicted.",
        "",
        "| actual \\ predicted | " + " | ".join(metadata["labels"]) + " |",
        "|---|" + "|".join("---" for _ in metadata["labels"]) + "|",
    ]
    matrix = results["fine_tuned"]["confusion_matrix"]
    for label, row in zip(metadata["labels"], matrix):
        lines.append(f"| {label} | " + " | ".join(str(value) for value in row) + " |")

    return "\n".join(lines)


def main():
    if not (MODEL_DIR / "finetuned_model.npz").exists():
        print("Models not found; running training first.")
        from train import main as train_main

        train_main()

    if not (DATA_DIR / "validation.jsonl").exists():
        prepare()

    validation = load_jsonl(DATA_DIR / "validation.jsonl")
    X_val = vectorize_many([row["text"] for row in validation])
    y_val, _ = encode_labels([row["label"] for row in validation])

    metadata = json.loads((MODEL_DIR / "training_metadata.json").read_text(encoding="utf-8"))

    models = {
        "pretrained": MLP.load(MODEL_DIR / "pretrained_model.npz"),
        "fine_tuned": MLP.load(MODEL_DIR / "finetuned_model.npz"),
    }

    results = {}
    print("=" * 60)
    print("        FINE-TUNING EVALUATION")
    print("=" * 60)

    for name, model in models.items():
        results[name] = evaluate_model(model, X_val, y_val)
        print(
            f"\n{name:<12} accuracy={results[name]['accuracy'] * 100:>6.1f}%  "
            f"macro_f1={results[name]['macro_f1']:.3f}"
        )

    print("\nFINE-TUNED PER-CLASS METRICS")
    print("-" * 60)
    for label in metadata["labels"]:
        metrics = results["fine_tuned"]["per_class"][label]
        print(
            f"{label:<10} precision={metrics['precision']:.3f} "
            f"recall={metrics['recall']:.3f} f1={metrics['f1-score']:.3f} "
            f"support={int(metrics['support'])}"
        )

    print("\nCONFUSION MATRIX (fine-tuned, rows=actual)")
    print("-" * 60)
    print("            " + " ".join(f"{label[:8]:>8}" for label in metadata["labels"]))
    for label, row in zip(metadata["labels"], results["fine_tuned"]["confusion_matrix"]):
        print(f"{label:<12}" + " ".join(f"{value:>8}" for value in row))

    payload = {
        "dataset": {
            "generic_rows": metadata["generic_rows"],
            "train_rows": metadata["train_rows"],
            "validation_rows": metadata["validation_rows"],
            "labels": metadata["labels"],
        },
        "training": {
            "pretraining": metadata["pretraining"],
            "fine_tuning": metadata["fine_tuning"],
            "improvement": metadata["improvement"],
        },
        "evaluation": results,
    }

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    (RESULT_DIR / "fine_tuning_results.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    (RESULT_DIR / "fine_tuning_report.md").write_text(
        _markdown(results, metadata), encoding="utf-8"
    )
    print(f"\nSaved evaluation to {RESULT_DIR}")


if __name__ == "__main__":
    main()
