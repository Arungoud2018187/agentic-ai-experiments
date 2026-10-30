"""Deterministic vision model for the visual QA experiment.

Segments foreground objects from the background, counts connected
components and classifies each component's colour and shape using
geometry (fill ratio, row-width profile, aspect ratio) and HSV colour.
"""

from collections import deque
from pathlib import Path

import colorsys
import numpy as np
from PIL import Image

MIN_AREA = 40


def _color_name(rgb):
    r, g, b = [value / 255.0 for value in rgb]
    hue, saturation, value = colorsys.rgb_to_hsv(r, g, b)
    hue *= 360

    if saturation < 0.18:
        if value < 0.25:
            return "black"
        if value < 0.75:
            return "gray"
        return "white"

    if hue < 15 or hue >= 345:
        return "red"
    if hue < 42:
        return "orange"
    if hue < 70:
        return "yellow"
    if hue < 160:
        return "green"
    if hue < 200:
        return "teal"
    if hue < 260:
        return "blue"
    if hue < 345:
        return "purple"
    return "unknown"


def _classify_shape(mask, bbox):
    x0, y0, x1, y1 = bbox
    width = x1 - x0 + 1
    height = y1 - y0 + 1
    component = mask[y0 : y1 + 1, x0 : x1 + 1]
    area = int(component.sum())
    fill = area / (width * height)
    aspect = width / height if height else 1.0

    row_widths = component.sum(axis=1)
    active_rows = row_widths[row_widths > 0]
    if len(active_rows) < 5:
        return "unknown"

    top_width = active_rows[: max(1, len(active_rows) // 5)].mean()
    bottom_width = active_rows[-max(1, len(active_rows) // 5) :].mean()

    if fill >= 0.85:
        return "square" if 0.8 <= aspect <= 1.25 else "rectangle"

    if fill >= 0.62 and 0.8 <= aspect <= 1.25:
        return "circle"

    if bottom_width > top_width * 1.5 and fill >= 0.4:
        return "triangle"

    return "star"


def _components(mask):
    height, width = mask.shape
    visited = np.zeros_like(mask, dtype=bool)
    components = []

    for y in range(height):
        for x in range(width):
            if not mask[y, x] or visited[y, x]:
                continue

            queue = deque([(y, x)])
            visited[y, x] = True
            pixels = []

            while queue:
                cy, cx = queue.popleft()
                pixels.append((cy, cx))

                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if (
                        0 <= ny < height
                        and 0 <= nx < width
                        and mask[ny, nx]
                        and not visited[ny, nx]
                    ):
                        visited[ny, nx] = True
                        queue.append((ny, nx))

            if len(pixels) >= MIN_AREA:
                ys = [pixel[0] for pixel in pixels]
                xs = [pixel[1] for pixel in pixels]
                components.append(
                    {
                        "pixels": pixels,
                        "bbox": (min(xs), min(ys), max(xs), max(ys)),
                        "area": len(pixels),
                    }
                )

    return sorted(components, key=lambda item: item["area"], reverse=True)


class VisionModel:
    name = "VisionModel"

    def analyze(self, path):
        image = Image.open(path).convert("RGB")
        pixels = np.asarray(image, dtype=np.int16)

        background = pixels[0, 0].astype(np.int16)
        distance = np.abs(pixels - background).sum(axis=2)
        mask = distance > 45

        components = _components(mask)
        objects = []

        for component in components:
            x0, y0, x1, y1 = component["bbox"]
            component_pixels = pixels[[y for y, _ in component["pixels"]], [x for _, x in component["pixels"]]]
            mean_color = component_pixels.mean(axis=0)
            color = _color_name(mean_color)
            shape = _classify_shape(mask, component["bbox"])

            # Purity: lower colour variance means a more confident label.
            purity = 1.0 - min(1.0, component_pixels.std(axis=0).mean() / 80.0)

            objects.append(
                {
                    "shape": shape,
                    "color": color,
                    "area": component["area"],
                    "bbox": list(component["bbox"]),
                    "mean_rgb": [round(float(value), 1) for value in mean_color],
                    "confidence": round(0.7 + 0.25 * purity, 2),
                }
            )

        return {
            "path": str(path),
            "filename": Path(path).name,
            "width": image.width,
            "height": image.height,
            "background_rgb": [int(value) for value in background],
            "object_count": len(objects),
            "objects": objects,
            "dominant_color": objects[0]["color"] if objects else "none",
            "dominant_shape": objects[0]["shape"] if objects else "none",
            "description": self.describe(objects),
        }

    @staticmethod
    def describe(objects):
        if not objects:
            return "The image contains no salient foreground objects."

        parts = []
        for item in objects:
            parts.append(f"a {item['color']} {item['shape']}")
        return "The image contains " + ", ".join(parts) + "."
