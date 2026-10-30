# Experiment 12 — Capstone: Multi-Agent AI Assistant

A full-stack, production-shaped capstone that unifies the previous experiments:
**text-to-SQL**, **retrieval-augmented QA**, and **research synthesis** behind one
chat interface, coordinated by a supervisor agent.

The demo runs completely offline with deterministic tools. An Ollama or
OpenAI-compatible model can optionally polish the final answer.

![architecture](https://img.shields.io/badge/stack-FastAPI%20%2B%20React-5eead4)

## Architecture

```
┌────────────────────────────┐
│  React + Vite dashboard    │
│  chat · agent mesh · trace │
└─────────────┬──────────────┘
              │ POST /api/chat
┌─────────────▼──────────────┐
│  FastAPI + Supervisor      │
│  routing · composition     │
│  citations · audit trace   │
└───┬─────────┬─────────┬────┘
    │         │         │
┌───▼───┐ ┌───▼────┐ ┌──▼────────┐
│ SQL   │ │ RAG    │ │ Research  │
│ agent │ │ agent  │ │ agent     │
└───┬───┘ └───┬────┘ └──┬────────┘
    │         │         │
 SQLite    BM25 KB    simulated web
 120 rows  10 docs    index + KB
```

- **SQL agent** — offline text-to-SQL over customers, products, orders and
  support tickets; read-only enforcement.
- **RAG agent** — BM25 retrieval with paragraph coverage and cited answers.
- **Research agent** — simulated web search combined with internal context.
- **Supervisor** — scores routing signals, combines agents for compound
  questions, deduplicates sources and emits a tool trace.
- **LLM layer** — `offline` (default), `ollama`, `openai`, or `auto`; the answer
  is always grounded in tool output.

## Quick start

### 1. Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API: <http://localhost:8000> · Swagger: <http://localhost:8000/docs>

### 2. Frontend (development)

```bash
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173>. Vite proxies `/api` to the backend.

### 3. Production-style single server

```bash
cd frontend && npm run build
cd ../backend && uvicorn app.main:app --port 8000
```

FastAPI serves `frontend/dist` at <http://localhost:8000>.

### Docker

```bash
docker compose up --build
```

Open <http://localhost:8000>. The image builds the React app, installs the
Python API, and runs as a single container.

## Demo questions

- What was total revenue in 2025?
- Which five customers generated the most revenue?
- How many cancelled orders do we have?
- What is the average order value?
- Which products sell best?
- What is the refund policy?
- Tell me about security and compliance.
- Summarize the latest agentic AI market trends and best practices.
- How many cancelled orders do we have **and** what is the refund policy?
- How many open support tickets are there **and** what is our SLA?

Compound questions route to multiple specialists and return a combined answer.

## Example response

```json
{
  "question": "How many cancelled orders do we have and what is the refund policy?",
  "agents": ["sql", "rag"],
  "answer": "Operational data:\nThere are 12 cancelled orders.\n\nKnowledge base:\nAnnual plans can be cancelled within 30 days...",
  "confidence": 0.947,
  "sources": [
    {"type": "database", "title": "NovaDesk demo SQLite database"},
    {"type": "knowledge_base", "title": "Refund and cancellation policy"}
  ],
  "tool_calls": [
    {"tool": "sql.query", "status": "success", "latency_ms": 1.1},
    {"tool": "knowledge.search", "status": "success", "latency_ms": 1.5}
  ]
}
```

## Verification

- `pytest` — **7 passed** (health, agents, SQL, RAG, research, multi-agent,
  validation).
- `npm run build` — Vite production bundle built successfully.
- Live server check — `/`, `/api/health`, `/api/chat` and static assets returned
  HTTP 200; the built UI rendered with no console errors.
- End-to-end browser interaction — clicking a suggested question returned a SQL
  answer, source card and execution trace.

## Layout

```
12_capstone/
├── backend/
│   ├── app/
│   │   ├── agents/        # sql_agent, rag_agent, research_agent, supervisor
│   │   ├── api/           # chat, health
│   │   ├── data/          # knowledge_base.json, web_index.json
│   │   ├── models/llm.py
│   │   ├── tools/         # database, retrieval, web_search
│   │   ├── config.py
│   │   └── main.py
│   ├── tests/test_api.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/    # Chat, Response, AgentStatus, ToolPanel
│   │   ├── pages/Dashboard.jsx
│   │   ├── services/api.js
│   │   ├── App.jsx
│   │   └── styles.css
│   ├── index.html
│   └── package.json
├── docker/Dockerfile
├── docker-compose.yml
└── .env.example
```

## Design notes and limitations

- The SQL planner is rule-based by design so the demo is deterministic and
  offline. Swap in an LLM or a semantic parser for broader coverage.
- The web index is simulated (`example.com` URLs). `tools/web_search.py` is the
  adapter boundary for a real search API.
- The LLM synthesis layer is optional. When offline, the supervisor composes the
  final answer from grounded agent output.
- No authentication is included; add OAuth/JWT and per-user tool scopes before
  exposing the API.
- SQL is read-only and the demo database is disposable. For production, use
  migrations, row-level authorization and a query timeout.
