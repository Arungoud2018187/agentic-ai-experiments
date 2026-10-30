"""Baseline model and synthetic dataset for the model-optimization experiment.

The workload is a small support-ticket intent classifier. A hashing
vectorizer turns text into a fixed-size numeric vector and a two-layer
NumPy MLP learns the six intents. Everything is deterministic so the
optimization comparison can be reproduced without a GPU or model server.
"""

import hashlib
import json
import re
from pathlib import Path

import numpy as np

DIMENSION = 384
HIDDEN = 128
LABELS = ["account", "billing", "general", "refund", "shipping", "technical"]

_WORD_RE = re.compile(r"[a-z0-9]+")

_TEMPLATES = {
    "account": [
        "i forgot my password and cannot sign in",
        "please reset the password for my account",
        "my account is locked after too many attempts",
        "how do i change the email address on my account",
        "i need to enable two factor authentication",
        "update the name on my profile",
        "i cannot log in with my username",
        "someone accessed my account without permission",
        "help me recover my login credentials",
        "how do i delete my account permanently",
        "the verification code is not arriving",
        "i want to change my account password",
        "my profile settings will not save",
        "please unlock my user account",
        "how do i add another user to my account",
        "i am locked out of the dashboard",
    ],
    "billing": [
        "i was charged twice for invoice {order}",
        "my credit card was billed {amount} today",
        "please explain the charge of {amount} on my statement",
        "why is my invoice higher this month",
        "i need a copy of my billing statement",
        "the payment on my account was declined",
        "my subscription price changed without notice",
        "send me the receipt for invoice {order}",
        "i see an unknown charge on my card",
        "update the payment method for my subscription",
        "when will my card be charged",
        "the invoice total does not match my plan",
        "i was overcharged on the last bill",
        "cancel the recurring payment on my card",
        "my billing address is wrong",
        "why did the annual plan renew early",
    ],
    "general": [
        "what are your support hours",
        "do you have a mobile app",
        "how can i contact the sales team",
        "tell me about your pricing plans",
        "where is your company headquartered",
        "thank you for your help today",
        "can i schedule a product demo",
        "do you offer a free trial",
        "how does the referral program work",
        "what integrations do you support",
        "is there a community forum",
        "how do i unsubscribe from the newsletter",
        "what is the status of your service",
        "can i use the product for my team",
        "where can i find documentation",
        "please share your privacy policy",
    ],
    "refund": [
        "i want a refund for order {order}",
        "how do i return this item and get my money back",
        "my refund has not arrived after {days} days",
        "cancel my purchase and refund the payment",
        "the product is defective so i need a refund",
        "what is the status of my refund request",
        "i returned the package please process my refund",
        "i was charged after cancelling and want the money back",
        "request a full refund for the annual plan",
        "the refund amount is wrong",
        "can i get a refund instead of a replacement",
        "how long does a refund take",
        "i changed my mind and want to return the order",
        "please reverse the charge and refund me",
        "my return was delivered but no refund was issued",
        "i need a refund for the duplicate purchase",
    ],
    "shipping": [
        "where is my package for order {order}",
        "the tracking number is not updating",
        "my delivery is late by {days} days",
        "my order has not arrived yet",
        "please change the shipping address for order {order}",
        "the package was shipped to the wrong address",
        "when will order {order} be delivered",
        "my parcel is stuck in transit",
        "can i upgrade to express shipping",
        "the box arrived damaged during shipping",
        "i need the tracking link for my order",
        "my order shows delivered but i never received it",
        "change the delivery date for my parcel",
        "why is shipment delayed",
        "the courier could not find my address",
        "ship my order to a different address",
    ],
    "technical": [
        "the app crashes when i open settings",
        "i get an error message on login",
        "the dashboard loads a blank page",
        "sync is not working on my phone",
        "the api returns error {error}",
        "the upload button does nothing",
        "the website is extremely slow",
        "i cannot connect to the service",
        "the report export fails every time",
        "notifications are not being delivered",
        "the integration keeps disconnecting",
        "i see a server error {error} in the browser",
        "the search feature returns no results",
        "video calls freeze after a few minutes",
        "the mobile app will not install",
        "data is missing from the analytics page",
    ],
}

_SLOTS = {
    "order": ["1042", "2077", "3185", "4420", "5519", "6034", "7781", "8190"],
    "amount": ["$19.99", "$49.00", "$120.50", "$240.00", "$9.99", "$89.95"],
    "days": ["2", "3", "5", "7", "10", "14"],
    "error": ["500", "502", "403", "404", "timeout"],
}


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


def generate_dataset(samples_per_class=120, seed=42):
    """Create deterministic, lightly noised support-ticket text."""
    rng = np.random.default_rng(seed)
    texts = []
    labels = []

    prefixes = ["", "hi team, ", "hello, ", "urgent: ", "quick question: "]
    suffixes = ["", " please help.", " thanks.", " as soon as possible."]

    for label in LABELS:
        templates = _TEMPLATES[label]
        for index in range(samples_per_class):
            template = templates[index % len(templates)]
            filled = template
            for slot, values in _SLOTS.items():
                token = "{" + slot + "}"
                if token in filled:
                    filled = filled.replace(token, values[rng.integers(len(values))])
            text = prefixes[rng.integers(len(prefixes))] + filled + suffixes[rng.integers(len(suffixes))]
            texts.append(text)
            labels.append(label)

    order = rng.permutation(len(texts))
    return [texts[index] for index in order], [labels[index] for index in order]


def encode_labels(labels, label_names=None):
    label_names = label_names or LABELS
    mapping = {label: index for index, label in enumerate(label_names)}
    return np.array([mapping[label] for label in labels], dtype=np.int64), label_names


def split_dataset(texts, labels, train_ratio=0.7, validation_ratio=0.15):
    total = len(texts)
    train_end = int(total * train_ratio)
    validation_end = train_end + int(total * validation_ratio)
    return {
        "train": (texts[:train_end], labels[:train_end]),
        "validation": (texts[train_end:validation_end], labels[train_end:validation_end]),
        "test": (texts[validation_end:], labels[validation_end:]),
    }


class MLP:
    """Two-layer ReLU classifier with Adam and softmax cross-entropy."""

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
                print(f"  epoch {epoch + 1:>3}/{epochs}  loss={average_loss:.4f}  accuracy={accuracy:.3f}")

        return self

    def clone(self):
        model = MLP(self.W1.shape[0], self.W1.shape[1], self.W2.shape[1])
        model.W1 = self.W1.copy()
        model.b1 = self.b1.copy()
        model.W2 = self.W2.copy()
        model.b2 = self.b2.copy()
        model.label_names = list(self.label_names)
        model.history = list(self.history)
        return model

    def parameter_count(self):
        return int(self.W1.size + self.b1.size + self.W2.size + self.b2.size)

    def size_bytes(self):
        return int(self.W1.nbytes + self.b1.nbytes + self.W2.nbytes + self.b2.nbytes)

    def summary(self):
        return {
            "input_dim": int(self.W1.shape[0]),
            "hidden_dim": int(self.W1.shape[1]),
            "output_dim": int(self.W2.shape[1]),
            "parameters": self.parameter_count(),
            "float32_size_bytes": self.size_bytes(),
            "labels": self.label_names,
        }

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
        model = cls(data["W1"].shape[0], data["W1"].shape[1], data["W2"].shape[1])
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


def build_datasets(samples_per_class=120, seed=42):
    texts, labels = generate_dataset(samples_per_class, seed=seed)
    split = split_dataset(texts, labels)
    datasets = {}
    for name, (split_texts, split_labels) in split.items():
        X = vectorize_many(split_texts)
        y, _ = encode_labels(split_labels)
        datasets[name] = {"X": X, "y": y, "texts": split_texts, "labels": split_labels}
    return datasets


def train_baseline(samples_per_class=120, epochs=30, seed=42, verbose=True):
    datasets = build_datasets(samples_per_class, seed=seed)
    model = MLP(seed=seed)
    model.fit(
        datasets["train"]["X"],
        datasets["train"]["y"],
        epochs=epochs,
        batch_size=32,
        learning_rate=0.01,
        seed=seed,
        verbose=verbose,
    )
    metrics = {}
    for name in ("train", "validation", "test"):
        predictions = model.predict(datasets[name]["X"])
        metrics[name] = {
            "accuracy": round(float((predictions == datasets[name]["y"]).mean()), 4),
            "samples": int(len(predictions)),
        }
    return model, datasets, metrics
