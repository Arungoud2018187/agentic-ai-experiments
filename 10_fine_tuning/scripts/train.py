"""Pretrain on a generic incident corpus, then fine-tune on the domain corpus."""

import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "models"

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mlp import MLP, encode_labels, vectorize_many  # noqa: E402
from prepare_dataset import load_jsonl, prepare  # noqa: E402


def _accuracy(model, X, y):
    return float((model.predict(X) == y).mean())


def main():
    if not (DATA_DIR / "train.jsonl").exists():
        prepare()

    generic = load_jsonl(DATA_DIR / "generic_train.jsonl")
    train = load_jsonl(DATA_DIR / "train.jsonl")
    validation = load_jsonl(DATA_DIR / "validation.jsonl")

    X_generic = vectorize_many([row["text"] for row in generic])
    y_generic, labels = encode_labels([row["label"] for row in generic])

    X_train = vectorize_many([row["text"] for row in train])
    y_train, _ = encode_labels([row["label"] for row in train])

    X_val = vectorize_many([row["text"] for row in validation])
    y_val, _ = encode_labels([row["label"] for row in validation])

    print("=" * 60)
    print("        FINE-TUNING FOR DOMAIN ADAPTATION")
    print("=" * 60)
    print(f"Generic corpus : {len(generic)} rows")
    print(f"Domain train   : {len(train)} rows")
    print(f"Validation     : {len(validation)} rows")
    print(f"Labels         : {labels}")

    print("\n[1/2] Pretraining on the generic corpus...")
    base = MLP(seed=42)
    base.fit(
        X_generic,
        y_generic,
        epochs=50,
        batch_size=32,
        learning_rate=0.01,
        seed=42,
    )
    base_val_accuracy = _accuracy(base, X_val, y_val)
    print(f"Pretrained validation accuracy: {base_val_accuracy:.3f}")

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    base.save(MODEL_DIR / "pretrained_model.npz")

    print("\n[2/2] Fine-tuning on the domain corpus...")
    finetuned = MLP(seed=43)
    finetuned.W1 = base.W1.copy()
    finetuned.b1 = base.b1.copy()
    finetuned.W2 = base.W2.copy()
    finetuned.b2 = base.b2.copy()
    finetuned.label_names = list(base.label_names)

    finetuned.fit(
        X_train,
        y_train,
        epochs=40,
        batch_size=32,
        learning_rate=0.003,
        seed=43,
    )
    fine_val_accuracy = _accuracy(finetuned, X_val, y_val)
    print(f"Fine-tuned validation accuracy: {fine_val_accuracy:.3f}")

    finetuned.save(MODEL_DIR / "finetuned_model.npz")

    metadata = {
        "generic_rows": len(generic),
        "train_rows": len(train),
        "validation_rows": len(validation),
        "labels": labels,
        "pretraining": {
            "epochs": 50,
            "learning_rate": 0.01,
            "validation_accuracy": round(base_val_accuracy, 4),
            "history": base.history,
        },
        "fine_tuning": {
            "epochs": 40,
            "learning_rate": 0.003,
            "validation_accuracy": round(fine_val_accuracy, 4),
            "history": finetuned.history,
        },
        "model_summary": finetuned.summary(),
        "improvement": round(fine_val_accuracy - base_val_accuracy, 4),
    }

    metadata_path = MODEL_DIR / "training_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"\nImprovement over the generic baseline: {metadata['improvement']:+.3f}")
    print(f"Saved models to {MODEL_DIR}")
    print(f"Saved training metadata to {metadata_path}")


if __name__ == "__main__":
    main()
