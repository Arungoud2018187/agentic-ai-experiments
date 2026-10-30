# Experiment 8 - Image Retrieval / Visual QA System

## Aim
Build a dependency-light visual retrieval and question-answering system
that classifies colours, shapes and object counts, retrieves similar
images and answers natural-language questions with evidence.

## Pipeline
```
images/ -> ImageEncoder -> feature index (colour histogram + 4x4 grid)
                    |
                    +-> VisionModel -> objects (colour, shape, bbox, count)
                                      |
question -> VisualQASystem -> VisualRetriever -> answer + evidence
```

## Files
| File | Purpose |
|------|---------|
| `src/dataset.py` | Generates a deterministic demo image set and labels |
| `src/image_encoder.py` | Colour histogram + spatial grid feature vector |
| `src/vision_model.py` | Background subtraction, connected components, shape/colour classification |
| `src/retriever.py` | Image-to-image cosine search and text/metadata filters |
| `src/qa.py` | Question parsing and grounded answers |
| `main.py` | Index building, classification evaluation, demo QA |

## Shape classification
| Feature | Used for |
|---------|----------|
| Fill ratio (area / bbox area) | square, rectangle, circle, triangle, star |
| Row-width profile | distinguishes triangle from star |
| Aspect ratio | square vs rectangle |
| HSV of mean object colour | red / blue / green / yellow / purple / orange / teal |

## Run
```bash
python main.py
python main.py --question "How many shapes are in image 6?"
python main.py --similar images/01_red_circle.png
```

## Output
`results/visual_qa_results.json` contains per-image analysis, retrieval
evidence, QA answers and classification accuracy against the labels.
