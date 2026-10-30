# Experiment 2 - RAG-Based Question Answering System

## Aim
Build a Retrieval Augmented Generation (RAG) pipeline that answers
questions from a local document collection and cites the retrieved
sources.

## Architecture

```
data/*.txt
   |  loader.py
   v
documents -> chunker.py -> chunks (500 chars, 100 overlap)
                               |
                               v
                     embeddings.py (MiniLM or hashing fallback)
                               |
                               v
                     retriever.py (FAISS or NumPy cosine)
                               |
 question ---------------------+
       |                       v
       |                 top-k chunks
       |                       |
       v                       v
              generator.py (Ollama / extractive fallback)
                       |
                       v
                grounded answer + citations
```

## Files
| File | Purpose |
|------|---------|
| `src/loader.py` | Loads `.txt` documents from `data/` |
| `src/chunker.py` | Splits documents into overlapping chunks |
| `src/embeddings.py` | SentenceTransformer embeddings, offline hashing fallback |
| `src/retriever.py` | Cosine-similarity vector search (FAISS/NumPy) |
| `src/generator.py` | Context-grounded answer generation |
| `main.py` | CLI pipeline and demo runner |

## Run
```bash
python main.py --demo
python main.py --question "How does RAG work?"
```

Optional model server:
```bash
ollama pull qwen3:8b
ollama serve
```
Without Ollama the system uses the extractive fallback, which is fully
offline and demonstrates retrieval-grounded answering.

## Output
`results/rag_results.json` contains each question, answer and the ranked
sources with similarity scores.
