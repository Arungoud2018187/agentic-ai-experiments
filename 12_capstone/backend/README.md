# Capstone Backend — Multi-Agent Assistant API

FastAPI backend for the NovaDesk capstone. A supervisor routes each question to
one or more specialist agents and returns a grounded answer with sources and an
audit-ready tool trace.

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Agent, database, knowledge-base and LLM status |
| `GET` | `/api/agents` | Agent registry and tool descriptions |
| `GET` | `/api/examples` | Suggested demo questions |
| `POST` | `/api/chat` | Run the supervisor and return an answer |
| `GET` | `/docs` | OpenAPI / Swagger UI |

### Chat request

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How many cancelled orders do we have and what is the refund policy?"}'
```

The response includes `answer`, `agents`, `routing`, `confidence`, `sources`,
`tool_calls`, structured `data`, and the LLM provider metadata.

## Agents and tools

- **SQL agent** — offline text-to-SQL planner over a seeded SQLite database
  (`customers`, `products`, `orders`, `tickets`). Read-only queries only.
- **RAG agent** — BM25 retrieval over 10 NovaDesk documents with extractive,
  cited answers.
- **Research agent** — search over a simulated web index plus internal context.
- **Supervisor** — keyword routing, multi-agent composition for compound
  questions, and deterministic synthesis when no LLM is configured.

## Run locally

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The database is created and seeded automatically at
`backend/data/demo.db`. No model server is required; the default
`LLM_PROVIDER=offline` uses deterministic rules.

## Test

```bash
cd backend
pytest
```

The suite covers health, agent discovery, SQL, RAG, research, multi-agent
routing and request validation.

## Configuration

| Variable | Default | Description |
| --- | --- | --- |
| `LLM_PROVIDER` | `offline` | `offline`, `ollama`, `openai`, or `auto` |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama endpoint |
| `OLLAMA_MODEL` | `llama3.2` | Ollama model name |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | OpenAI-compatible endpoint |
| `OPENAI_API_KEY` | empty | API key for the compatible endpoint |
| `OPENAI_MODEL` | `gpt-4o-mini` | Model name |
| `DATABASE_PATH` | `backend/data/demo.db` | SQLite file |
| `CORS_ORIGINS` | localhost:5173/8000 | Comma-separated browser origins |
| `STATIC_DIR` | `frontend/dist` | Built SPA directory |

`auto` tries Ollama first, then an OpenAI-compatible endpoint when a key is
present, and finally falls back to offline rules.

## Layout

```
backend/
├── app/
│   ├── config.py
│   ├── main.py
│   ├── agents/          # sql, rag, research, supervisor
│   ├── api/             # health, chat
│   ├── models/llm.py    # Ollama / OpenAI / offline client
│   ├── tools/           # database, retrieval, web_search
│   └── data/            # knowledge_base.json, web_index.json
├── tests/test_api.py
├── pytest.ini
└── requirements.txt
```

## Safety notes

- SQL execution rejects anything that is not a single read-only `SELECT`/`WITH`.
- The web index is simulated and local; replace `tools/web_search.py` with a real
  provider adapter for production.
- The LLM only synthesizes tool output. Authorization and data access remain in
  application code.
