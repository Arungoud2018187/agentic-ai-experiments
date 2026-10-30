"""Image encoder and visual feature extractor.

Builds a compact feature vector from colour histograms, spatial colour
grids and global statistics.  This is dependency light (Pillow + NumPy)
and works without downloading a CLIP checkpoint.
"""

from pathlib import Path

import numpy as np
from PIL import Image

FEATURE_SIZE = 3 * 4 * 4 + 4 * 4 * 3 + 6 + 1


def _load(path):
    image = Image.open(path).convert("RGB")
    return image


def encode_image(path):
    image = _load(path).resize((64, 64))
    pixels = np.asarray(image, dtype=np.float32) / 255.0

    # Colour histogram, 4 bins per channel.
    histogram = []
    for channel in range(3):
        counts, _ = np.histogram(pixels[:, :, channel], bins=4, range=(0.0, 1.0))
        histogram.extend(counts / counts.sum())

    # 4x4 spatial colour grid.
    grid = []
    for row in range(4):
        for col in range(4):
            block = pixels[row * 16 : (row + 1) * 16, col * 16 : (col + 1) * 16]
            grid.extend(block.reshape(-1, 3).mean(axis=0).tolist())

    means = pixels.reshape(-1, 3).mean(axis=0).tolist()
    stds = pixels.reshape(-1, 3).std(axis=0).tolist()
    aspect = image.width / image.height if image.height else 1.0

    vector = np.array(histogram + grid + means + stds + [aspect], dtype=np.float32)
    return vector


def normalize(vector):
    norm = np.linalg.norm(vector)
    return vector / norm if norm else vector


class ImageEncoder:
    name = "ImageEncoder"

    def encode(self, path):
        return normalize(encode_image(path))

    def encode_many(self, paths):
        return np.vstack([self.encode(path) for path in paths]).astype(np.float32)

    def encode_directory(self, directory):
        paths = sorted(
            path
            for path in Path(directory).glob("*")
            if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
        )
        return paths, self.encode_many(paths)
