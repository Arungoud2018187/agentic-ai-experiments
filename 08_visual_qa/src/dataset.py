"""Deterministic demo image generator for the visual QA experiment.

Creates simple shape images and a label file used only for evaluation.
The vision model never reads the labels.
"""

import json
from pathlib import Path

from PIL import Image, ImageDraw

BASE_DIR = Path(__file__).resolve().parent.parent
IMAGES_DIR = BASE_DIR / "images"

BACKGROUND = (255, 255, 255)

COLORS = {
    "red": (220, 45, 45),
    "blue": (45, 85, 220),
    "green": (40, 170, 80),
    "yellow": (240, 200, 30),
    "purple": (140, 60, 200),
    "orange": (240, 130, 30),
    "teal": (30, 170, 170),
}


def _star_points(cx, cy, outer, inner, points=5):
    import math

    coordinates = []
    for index in range(points * 2):
        radius = outer if index % 2 == 0 else inner
        angle = -math.pi / 2 + index * math.pi / points
        coordinates.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    return coordinates


def _draw_shape(draw, shape, color, box):
    x0, y0, x1, y1 = box
    if shape == "circle":
        draw.ellipse(box, fill=color)
    elif shape == "square":
        draw.rectangle(box, fill=color)
    elif shape == "rectangle":
        draw.rectangle(box, fill=color)
    elif shape == "triangle":
        draw.polygon([(x0, y1), (x1, y1), ((x0 + x1) // 2, y0)], fill=color)
    elif shape == "star":
        cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
        radius = min(x1 - x0, y1 - y0) // 2
        draw.polygon(_star_points(cx, cy, radius, radius * 0.42), fill=color)


def _render(filename, background, shapes):
    image = Image.new("RGB", (256, 256), background)
    draw = ImageDraw.Draw(image)
    for shape in shapes:
        _draw_shape(draw, shape["shape"], shape["color"], shape["box"])
    image.save(IMAGES_DIR / filename)


def create_demo_images(force=False):
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    label_path = IMAGES_DIR / "labels.json"

    if label_path.exists() and not force:
        return json.loads(label_path.read_text(encoding="utf-8"))

    definitions = [
        ("01_red_circle.png", [{"shape": "circle", "color": COLORS["red"], "box": (58, 58, 198, 198)}]),
        ("02_blue_square.png", [{"shape": "square", "color": COLORS["blue"], "box": (58, 58, 198, 198)}]),
        ("03_green_triangle.png", [{"shape": "triangle", "color": COLORS["green"], "box": (48, 48, 208, 208)}]),
        ("04_yellow_star.png", [{"shape": "star", "color": COLORS["yellow"], "box": (48, 48, 208, 208)}]),
        ("05_purple_rectangle.png", [{"shape": "rectangle", "color": COLORS["purple"], "box": (38, 78, 218, 178)}]),
        (
            "06_red_circle_blue_square.png",
            [
                {"shape": "circle", "color": COLORS["red"], "box": (22, 88, 122, 188)},
                {"shape": "square", "color": COLORS["blue"], "box": (146, 88, 226, 168)},
            ],
        ),
        ("07_orange_circle.png", [{"shape": "circle", "color": COLORS["orange"], "box": (58, 58, 198, 198)}]),
        ("08_teal_triangle.png", [{"shape": "triangle", "color": COLORS["teal"], "box": (48, 48, 208, 208)}]),
    ]

    labels = {}
    for filename, shapes in definitions:
        _render(filename, BACKGROUND, shapes)
        labels[filename] = {
            "objects": [
                {
                    "shape": shape["shape"],
                    "color": _color_name(shape["color"]),
                }
                for shape in shapes
            ]
        }

    label_path.write_text(json.dumps(labels, indent=2), encoding="utf-8")
    return labels


def _color_name(rgb):
    r, g, b = rgb
    if r > 180 and g < 100 and b < 100:
        return "red"
    if g > 130 and b > 130 and r < 100:
        return "teal"
    if b > 160 and r < 110:
        return "blue"
    if g > 120 and r < 110 and b < 140:
        return "green"
    if r > 200 and g > 160 and b < 100:
        return "yellow"
    if r > 100 and b > 140 and g < 110:
        return "purple"
    if r > 200 and 90 < g < 180 and b < 90:
        return "orange"
    if g > 130 and b > 130 and r < 100:
        return "teal"
    return "unknown"


if __name__ == "__main__":
    print(create_demo_images(force=True))
