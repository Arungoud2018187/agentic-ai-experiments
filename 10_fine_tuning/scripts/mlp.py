"""Small NumPy MLP and hashing vectorizer for the fine-tuning experiment.

The model is deliberately small (256 -> 64 -> 5) so it trains in seconds
on a CPU while still demonstrating pretraining and domain fine-tuning.
"""

import hashlib
import json
import re
from pathlib import Path

import numpy as np

DIMENSION = 256
HIDDEN = 64
LABELS = ["benign", "ddos", "insider", "malware", "phishing"]

_WORD_RE = re.compile(r"[a-z0-9]+")


def tokenize(text):
    words = _WORD_RE.findall(text.lower())
    bigrams = [f"{a}_{b}" for a, b in zip(words, words[1:])]
    return words + bigrams


def vectorize(text, dimension=DIMENSION):
    vector = np.zeros(dimension, dtype=np.float32)
    tokens = tokenize(text)
    if not tokens:
        return vector

    counts = {}
    for token in tokens:
        counts[token] = counts.get(token, 0) + 1

    for token, count in counts.items():
        digest = hashlib.md5(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "little") % dimension
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign * (1.0 + np.log(count))

    norm = np.linalg.norm(vector)
    return vector / norm if norm else vector


def vectorize_many(texts):
    return np.vstack([vectorize(text) for text in texts]).astype(np.float32)


def encode_labels(labels, label_names=None):
    label_names = label_names or LABELS
    mapping = {label: index for index, label in enumerate(label_names)}
    return np.array([mapping[label] for label in labels], dtype=np.int64), label_names


class MLP:
    def __init__(self, input_dim=DIMENSION, hidden_dim=HIDDEN, output_dim=len(LABELS), seed=42):
        rng = np.random.default_rng(seed)
        self.W1 = rng.normal(0, np.sqrt(2.0 / input_dim), (input_dim, hidden_dim)).astype(np.float32)
        self.b1 = np.zeros(hidden_dim, dtype=np.float32)
        self.W2 = rng.normal(0, np.sqrt(2.0 / hidden_dim), (hidden_dim, output_dim)).astype(np.float32)
        self.b2 = np.zeros(output_dim, dtype=np.float32)
        self.label_names = list(LABELS)
        self.history = []

    def _forward(self, X):
        hidden = np.maximum(0, X @ self.W1 + self.b1)
        logits = hidden @ self.W2 + self.b2
        logits -= logits.max(axis=1, keepdims=True)
        exp = np.exp(logits)
        probabilities = exp / exp.sum(axis=1, keepdims=True)
        return hidden, probabilities

    def predict_proba(self, X):
        return self._forward(X)[1]

    def predict(self, X):
        return np.argmax(self.predict_proba(X), axis=1)

    def fit(self, X, y, epochs=30, batch_size=32, learning_rate=0.01, l2=1e-4, seed=42, verbose=True):
        rng = np.random.default_rng(seed)
        parameters = [self.W1, self.b1, self.W2, self.b2]
        first_moment = [np.zeros_like(p) for p in parameters]
        second_moment = [np.zeros_like(p) for p in parameters]
        beta1, beta2, epsilon = 0.9, 0.999, 1e-8
        step = 0

        self.history = []

        for epoch in range(epochs):
            order = rng.permutation(len(X))
            total_loss = 0.0

            for start in range(0, len(X), batch_size):
                indices = order[start : start + batch_size]
                X_batch = X[indices]
                y_batch = y[indices]

                hidden, probabilities = self._forward(X_batch)
                batch = len(indices)

                loss = -np.log(probabilities[np.arange(batch), y_batch] + 1e-9).mean()
                total_loss += loss * batch

                delta = probabilities.copy()
                delta[np.arange(batch), y_batch] -= 1
                delta /= batch

                dW2 = hidden.T @ delta + l2 * self.W2
                db2 = delta.sum(axis=0)
                dhidden = (delta @ self.W2.T) * (hidden > 0)
                dW1 = X_batch.T @ dhidden + l2 * self.W1
                db1 = dhidden.sum(axis=0)

                gradients = [dW1, db1, dW2, db2]
                step += 1

                for index, gradient in enumerate(gradients):
                    first_moment[index] = beta1 * first_moment[index] + (1 - beta1) * gradient
                    second_moment[index] = beta2 * second_moment[index] + (1 - beta2) * (gradient ** 2)
                    m_hat = first_moment[index] / (1 - beta1**step)
                    v_hat = second_moment[index] / (1 - beta2**step)
                    parameters[index] -= learning_rate * m_hat / (np.sqrt(v_hat) + epsilon)

            accuracy = float((self.predict(X) == y).mean())
            average_loss = total_loss / len(X)
            self.history.append(
                {"epoch": epoch + 1, "loss": round(float(average_loss), 4), "accuracy": round(accuracy, 4)}
            )

            if verbose and (epoch + 1) % 10 == 0:
                print(
                    f"  epoch {epoch + 1:>3}/{epochs}  loss={average_loss:.4f}  accuracy={accuracy:.3f}"
                )

        return self

    def save(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez(
            path,
            W1=self.W1,
            b1=self.b1,
            W2=self.W2,
            b2=self.b2,
            label_names=np.array(self.label_names),
            history=np.array(json.dumps(self.history)),
        )

    @classmethod
    def load(cls, path):
        data = np.load(path, allow_pickle=True)
        model = cls(
            input_dim=data["W1"].shape[0],
            hidden_dim=data["W1"].shape[1],
            output_dim=data["W2"].shape[1],
        )
        model.W1 = data["W1"]
        model.b1 = data["b1"]
        model.W2 = data["W2"]
        model.b2 = data["b2"]
        model.label_names = [str(item) for item in data["label_names"]]
        try:
            model.history = json.loads(str(data["history"]))
        except Exception:  # noqa: BLE001
            model.history = []
        return model

    def summary(self):
        return {
            "input_dim": int(self.W1.shape[0]),
            "hidden_dim": int(self.W1.shape[1]),
            "output_dim": int(self.W2.shape[1]),
            "parameters": int(self.W1.size + self.b1.size + self.W2.size + self.b2.size),
            "labels": self.label_names,
        }
