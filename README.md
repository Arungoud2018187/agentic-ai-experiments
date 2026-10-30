# Agentic AI Experiments

A complete, runnable lab series covering the agentic AI stack: text-to-SQL,
retrieval-augmented generation, prompt chaining, tool-using agents,
multi-agent orchestration, policy compliance, deep research, visual QA,
reasoning benchmarks, fine-tuning, model optimization and a full-stack
capstone.

All twelve experiments have been implemented, executed and captured with
outputs under their `results/` directories. The suite is **offline-first**:
no Ollama server, hosted API key or GPU is required for the recorded runs.
Experiments 1-4 and the capstone optionally use Ollama or any
OpenAI-compatible endpoint when one is available.

## Results at a glance

| # | Experiment | Focus | Captured result |
|---|------------|-------|-----------------|
| 1 | [Text-to-SQL](01_text_to_sql/) | Natural language to read-only SQLite | 5/5 demo questions answered with SQL and rows |
| 2 | [RAG Question Answering](02_rag_question_answering/) | Chunking, embeddings, retrieval, cited answers | 3 documents, 5 chunks, 4 grounded answers with sources |
| 3 | [Prompt Chaining](03_prompt_chaining/) | Four-stage extract -> analyse -> summarise -> report | Full incident report generated through all four stages |
| 4 | [SQL Agent](04_sql_agent/) | Plan, tool use, execute, answer | 4/4 questions answered with complete tool traces |
| 5 | [Multi-Agent SDR](05_multi_agent_sdr/) | Supervisor + lead generation, qualification, outreach | 10 leads, 8 qualified (80%), average score 74.0, $600k pipeline |
| 6 | [Policy Compliance](06_policy_compliance_agent/) | Declarative rules, risk scoring, explainable decisions | 10 policies, 12 records, 26 violations, 2 approve / 5 review / 5 reject |
| 7 | [Deep Research](07_deep_research_agent/) | Plan, research, reflect, synthesise | 4 sub-questions, 6 sources, coverage 1.00, cited report |
| 8 | [Image Retrieval / Visual QA](08_visual_qa/) | Colour/shape analysis, retrieval, grounded QA | 8/8 images classified correctly (100%), 6 QA scenarios |
| 9 | [Reasoning Benchmark](09_reasoning_benchmark/) | Zero-shot vs few-shot vs structured prompting | 25.0% -> 58.3% -> 100.0% on 12 questions |
| 10 | [Fine-Tuning](10_fine_tuning/) | Generic pretraining, domain fine-tuning | 48.8% -> 100.0% accuracy; macro-F1 0.461 -> 1.000 |
| 11 | [Model Optimization](11_model_optimization/) | INT8 quantization and structured pruning | 195.5 KB -> 24.7 KB (7.93x) at 100% accuracy |
| 12 | [Capstone](12_capstone/) | FastAPI + React multi-agent assistant | 7 tests pass, production build succeeds, live SQL + RAG response |

## Repository layout

```
agentic-ai-experiments/
├── 01_text_to_sql/               # schema-aware SQL generation and execution
├── 02_rag_question_answering/    # chunk -> embed -> retrieve -> answer
├── 03_prompt_chaining/           # four-step analysis chain
├── 04_sql_agent/                 # plan/execute/answer tool-using agent
├── 05_multi_agent_sdr/           # supervisor + three specialist agents
├── 06_policy_compliance_agent/   # policy engine and risk decisions
├── 07_deep_research_agent/       # planner, researcher, reflector, synthesiser
├── 08_visual_qa/                 # image features, classification, retrieval, QA
├── 09_reasoning_benchmark/       # prompting strategies and evaluation
├── 10_fine_tuning/               # NumPy MLP pretraining and domain adaptation
├── 11_model_optimization/        # quantization, pruning and benchmarks
├── 12_capstone/                  # full-stack multi-agent assistant
├── .venv/                        # shared Windows virtual environment (gitignored)
└── README.md
```

Each experiment keeps its own `README.md`, source tree, data and
`results/` evidence. Top-level `EXECUTION_REPORT.md` records the clean
rerun used for this snapshot.

## Setup

The recorded runs used Python 3.12 on Windows with a shared virtual
environment at the repository root:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install requests numpy scikit-learn fastapi uvicorn httpx pillow beautifulsoup4 pytest
```

The capstone frontend needs Node.js 18+:

```powershell
cd 12_capstone\frontend
npm install
```

Experiments 1-11 require only the Python packages above. Heavy optional
dependencies are replaced with lightweight, deterministic implementations
so the lab runs on a CPU without downloads.

## Running the experiments

Run each command from its experiment directory. From the repository root
on Windows, use the shared interpreter explicitly:

| # | Command |
|---|---------|
| 1 | `.venv\Scripts\python.exe 01_text_to_sql\main.py --demo` |
| 2 | `.venv\Scripts\python.exe 02_rag_question_answering\main.py --demo` |
| 3 | `.venv\Scripts\python.exe 03_prompt_chaining\main.py --demo` |
| 4 | `.venv\Scripts\python.exe 04_sql_agent\main.py --demo` |
| 5 | `.venv\Scripts\python.exe 05_multi_agent_sdr\main.py` |
| 6 | `.venv\Scripts\python.exe 06_policy_compliance_agent\main.py` |
| 7 | `.venv\Scripts\python.exe 07_deep_research_agent\main.py --demo` |
| 8 | `.venv\Scripts\python.exe 08_visual_qa\main.py` |
| 9 | `.venv\Scripts\python.exe 09_reasoning_benchmark\main.py` |
| 10 | `.venv\Scripts\python.exe 10_fine_tuning\scripts\prepare_dataset.py --force`, then `train.py`, then `evaluate.py` |
| 11 | `.venv\Scripts\python.exe 11_model_optimization\main.py` |
| 12 | `cd 12_capstone\backend && ..\..\.venv\Scripts\python.exe -m pytest -q`; `cd ..\frontend && npm run build`; `uvicorn app.main:app` |

For experiment 10, the three scripts must run in order from the
`10_fine_tuning` directory. For experiment 12, build the frontend first so
FastAPI can serve the SPA from `frontend/dist`.

## Offline-first model strategy

Experiments 1-4 share a provider layer with four modes:

| `LLM_PROVIDER` | Behaviour |
|----------------|-----------|
| `auto` | Try Ollama, then an OpenAI-compatible endpoint, then offline |
| `ollama` | Use `OLLAMA_URL` / `OLLAMA_MODEL` only |
| `openai` | Use `OPENAI_BASE_URL` / `OPENAI_MODEL` only |
| `offline` | Skip network calls and use deterministic logic |

Relevant environment variables are `OLLAMA_URL`, `OLLAMA_MODEL`,
`OPENAI_BASE_URL`, `OPENAI_API_KEY`, `OPENAI_MODEL` and `LLM_TIMEOUT`.
The capstone defaults to `LLM_PROVIDER=offline`; when a model is
configured it only polishes answers that are already grounded in tool
output.

Experiments 5-11 use deterministic local logic or lightweight NumPy
models by design, so recorded metrics are reproducible without a model
server.

## Evidence and verification

- Every experiment writes machine-readable results and console output to
  its `results/` directory (for example `results/run_output.txt`,
  `results/*.json` and generated reports).
- Experiment 12 includes `backend/tests/test_api.py` (7 tests) and
  captured `results/pytest_output.txt`, `results/frontend_build_output.txt`
  and `results/api_smoke_test.json`.
- The capstone was also exercised in a browser: a compound question
  returned a SQL result, a knowledge-base citation and an agent trace.

## Notes and limitations

- The deterministic fallbacks are intentionally narrow and explainable;
  they demonstrate the orchestration and evaluation plumbing rather than
  frontier-model quality.
- Recorded metrics come from small synthetic datasets, so they are
  reproducibility checks, not production benchmarks.
- Experiment 11 measures artifact-size reduction directly; its NumPy
  simulation dequantizes INT8 weights at load time, so wall-clock speedups
  would require specialized INT8 kernels.
- The capstone has no authentication and uses a disposable SQLite
  database; add OAuth/JWT, migrations and row-level authorization before
  production use.
- See each experiment's README for architecture, commands and
  experiment-specific caveats.
