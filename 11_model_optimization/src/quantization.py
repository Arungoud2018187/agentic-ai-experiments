"""Post-training optimization techniques: int8 quantization and pruning.

The simulation is intentionally dependency-free (NumPy only). Weights are
stored as int8 plus one float32 scale per tensor; biases are kept in
float32 because they are tiny. Pruning uses global magnitude thresholds
and reports both dense and sparse (CSR) storage estimates.
"""

import numpy as np

from .baseline import MLP


class Int8QuantizedModel:
    """Post-training symmetric per-tensor int8 quantization of weights."""

    def __init__(self, model):
        self.label_names = list(model.label_names)
        self.input_dim = int(model.W1.shape[0])
        self.hidden_dim = int(model.W1.shape[1])
        self.output_dim = int(model.W2.shape[1])

        self.weights = {}
        self.scales = {}
        for name in ("W1", "W2"):
            weight = getattr(model, name)
            scale = float(np.max(np.abs(weight)) / 127.0) or 1.0
            quantized = np.clip(np.round(weight / scale), -127, 127).astype(np.int8)
            self.weights[name] = quantized
            self.scales[name] = scale

        self.biases = {"b1": model.b1.astype(np.float32).copy(), "b2": model.b2.astype(np.float32).copy()}
        self.reference_size_bytes = model.size_bytes()
        self._dequantized = None

    def dequantize(self):
        model = MLP(self.input_dim, self.hidden_dim, self.output_dim)
        model.label_names = list(self.label_names)
        model.W1 = (self.weights["W1"].astype(np.float32) * self.scales["W1"]).astype(np.float32)
        model.W2 = (self.weights["W2"].astype(np.float32) * self.scales["W2"]).astype(np.float32)
        model.b1 = self.biases["b1"].copy()
        model.b2 = self.biases["b2"].copy()
        return model

    def model(self):
        if self._dequantized is None:
            self._dequantized = self.dequantize()
        return self._dequantized

    def predict(self, X):
        return self.model().predict(X)

    def size_bytes(self):
        total = sum(array.nbytes for array in self.weights.values())
        total += sum(array.nbytes for array in self.biases.values())
        total += 4 * len(self.scales)
        return int(total)

    def summary(self):
        return {
            "scheme": "symmetric per-tensor int8 (weights), float32 biases",
            "size_bytes": self.size_bytes(),
            "reference_size_bytes": self.reference_size_bytes,
            "compression_ratio": round(self.reference_size_bytes / self.size_bytes(), 3),
            "scales": {name: round(value, 8) for name, value in self.scales.items()},
        }


def quantize_model(model):
    return Int8QuantizedModel(model)


def quantization_error(original, quantized):
    """Relative Frobenius reconstruction error for each weight matrix."""
    errors = {}
    for name in ("W1", "W2"):
        reference = getattr(original, name).astype(np.float64)
        reconstructed = quantized.weights[name].astype(np.float64) * quantized.scales[name]
        denominator = np.linalg.norm(reference)
        relative = np.linalg.norm(reference - reconstructed) / denominator if denominator else 0.0
        errors[name] = {
            "relative_frobenius_error": round(float(relative), 6),
            "max_abs_error": round(float(np.max(np.abs(reference - reconstructed))), 6),
        }
    return errors


def magnitude_prune(model, sparsity=0.5):
    """Globally prune the smallest-magnitude weights in both linear layers."""
    if not 0.0 <= sparsity < 1.0:
        raise ValueError("sparsity must be in [0, 1)")

    pruned = model.clone()
    weights = np.concatenate([np.abs(pruned.W1).ravel(), np.abs(pruned.W2).ravel()])
    threshold = float(np.quantile(weights, sparsity))
    pruned.W1 = np.where(np.abs(pruned.W1) <= threshold, 0.0, pruned.W1).astype(np.float32)
    pruned.W2 = np.where(np.abs(pruned.W2) <= threshold, 0.0, pruned.W2).astype(np.float32)
    pruned.pruning = {
        "sparsity": sparsity,
        "threshold": threshold,
        "nonzero_weights": int(np.count_nonzero(pruned.W1) + np.count_nonzero(pruned.W2)),
        "total_weights": int(pruned.W1.size + pruned.W2.size),
    }
    return pruned


def structured_prune(model, fraction=0.5):
    """Remove the least important hidden units, shrinking both weight matrices.

    Unit importance is the product of the incoming and outgoing weight
    norms. Unlike magnitude pruning this reduces the dense dimensions, so
    it lowers both artifact size and inference cost.
    """
    if not 0.0 <= fraction < 1.0:
        raise ValueError("fraction must be in [0, 1)")

    importance = np.linalg.norm(model.W1, axis=0) * np.linalg.norm(model.W2, axis=1)
    keep_count = max(1, int(round(model.W1.shape[1] * (1.0 - fraction))))
    keep = np.argsort(importance)[-keep_count:]
    keep = np.sort(keep)

    pruned = MLP(model.W1.shape[0], keep_count, model.W2.shape[1])
    pruned.W1 = model.W1[:, keep].copy()
    pruned.b1 = model.b1[keep].copy()
    pruned.W2 = model.W2[keep, :].copy()
    pruned.b2 = model.b2.copy()
    pruned.label_names = list(model.label_names)
    pruned.history = list(model.history)
    pruned.pruning = {
        "type": "structured_hidden_units",
        "fraction": fraction,
        "kept_units": int(keep_count),
        "original_units": int(model.W1.shape[1]),
    }
    return pruned


def sparse_size_bytes(model, quantized=False):
    """Estimate CSR storage for the two weight matrices.

    CSR needs one value and one int32 column index per non-zero plus a
    row-pointer array. Quantized sparse values use int8.
    """
    total = 0
    for weight in (model.W1, model.W2):
        nonzero = int(np.count_nonzero(weight))
        value_bytes = 1 if quantized else 4
        total += nonzero * value_bytes + nonzero * 4 + (weight.shape[0] + 1) * 4
    total += model.b1.nbytes + model.b2.nbytes
    return int(total)


def sparsity(model):
    weights = np.concatenate([model.W1.ravel(), model.W2.ravel()])
    return round(1.0 - float(np.count_nonzero(weights)) / weights.size, 4)
