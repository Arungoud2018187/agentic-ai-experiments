# Execution Report

Date: 2026-10-30 (America/New_York)
Repository: `C:\Users\arung\OneDrive\Desktop\ARCH-BACKUP-2026\Home\Projects\agentic-ai-experiments`
Remote: `git@github.com:Arungoud2018187/agentic-ai-experiments.git`
Branch: `main`

## Environment

- OS: Windows 11 (win32)
- Python: 3.12.10 (shared root `.venv`)
- Packages: NumPy 2.5.4, scikit-learn 1.9.1, FastAPI 0.162.0, Node 24.21.0, npm 11.19.0
- No Ollama, OpenAI-compatible server, GPU, FAISS, sentence-transformers,
  PyTorch or CLIP was available. All runs used deterministic fallbacks
  and lightweight NumPy/Pillow implementations.
- Interpreter used for every Python run:
  `.venv\Scripts\python.exe`

## Clean rerun commands

All commands were run from their experiment directories unless noted.

```powershell
# Experiments 1-4 (batch/demo modes)
.venv\Scripts\python.exe main.py --demo

# Experiments 5-9 and 11
.venv\Scripts\python.exe main.py

# Experiment 8
.venv\Scripts\python.exe main.py

# Experiment 10
.venv\Scripts\python.exe scripts\prepare_dataset.py --force
.venv\Scripts\python.exe scripts\train.py
.venv\Scripts\python.exe scripts\evaluate.py

# Experiment 12
cd 12_capstone\backend
.venv\Scripts\python.exe -m pytest -q
cd ..\frontend
npm run build
cd ..\backend
uvicorn app.main:app --port 8000
```

Each standard experiment saved stdout to `results/run_output.txt`. Experiment 10
combined the three scripts into one `results/run_output.txt`.

## Experiment status

| # | Experiment | Status | Key captured result | Evidence |
|---|------------|--------|---------------------|----------|
| 1 | Text-to-SQL | Pass | 5/5 demo questions with SQL and rows | `01_text_to_sql/results/text_to_sql_results.json`, `results/run_output.txt` |
| 2 | RAG Question Answering | Pass | 4 questions, cited sources, top score 0.507 | `02_rag_question_answering/results/rag_results.json`, `results/run_output.txt` |
| 3 | Prompt Chaining | Pass | 4-stage incident report with citations | `03_prompt_chaining/results/prompt_chain_results.json`, `results/run_output.txt` |
| 4 | SQL Agent | Pass | 4/4 questions, SQL and tool traces | `04_sql_agent/results/sql_agent_results.json`, `results/run_output.txt` |
| 5 | Multi-Agent SDR | Pass | 10 leads, 8 qualified, 80%, avg 74.0, $600k pipeline | `05_multi_agent_sdr/results/sdr_campaign_report.json`, `results/run_output.txt` |
| 6 | Policy Compliance | Pass | 12 records, 26 violations, 2 approve / 5 review / 5 reject | `06_policy_compliance_agent/results/compliance_audit.json`, `results/run_output.txt` |
| 7 | Deep Research | Pass | 4 sub-questions, 6 sources, coverage 1.00 | `07_deep_research_agent/results/deep_research_results.json`, `deep_research_report.md`, `results/run_output.txt` |
| 8 | Image Retrieval / Visual QA | Pass | 8/8 images, 100% accuracy, 6 QA scenarios | `08_visual_qa/results/visual_qa_results.json`, `results/run_output.txt` |
| 9 | Reasoning Benchmark | Pass | zero-shot 25.0%, few-shot 58.3%, structured 100.0% | `09_reasoning_benchmark/results/reasoning_benchmark_results.json`, `results/run_output.txt` |
| 10 | Fine-Tuning | Pass | 48.8% -> 100.0% accuracy; macro-F1 0.461 -> 1.000 | `10_fine_tuning/results/fine_tuning_results.json`, `results/run_output.txt` |
| 11 | Model Optimization | Pass | 195.5 KB -> 24.7 KB (7.93x), 100% accuracy | `11_model_optimization/results/benchmark_results.json`, `model_optimization_report.md`, `results/run_output.txt` |
| 12 | Capstone | Pass | 7 tests, successful production build, live SQL + RAG response | `12_capstone/results/pytest_output.txt`, `frontend_build_output.txt`, `api_smoke_test.json` |

## Highlights and captured outputs

### Experiment 1 - Text-to-SQL
- Database: `departments`, `employees`, `projects`.
- Demo questions covered counts, aggregations, filters, joins, status filters
  and sorting.
- Offline planner generated all five queries, including
  `SELECT d.name AS department, COUNT(e.id) AS employee_count ...`
  and `SELECT SUM(budget) AS total_budget FROM projects WHERE status = 'Active'`.
- Result rows are saved in `text_to_sql_results.json`.

### Experiment 2 - RAG Question Answering
- Loaded 3 documents, created 5 chunks.
- Used the offline hashing embedder and NumPy cosine retrieval.
- Answered questions on agentic AI, RAG, hallucination causes and local
  model benefits, each with source citations.
- Saved chunk scores and retrieved text in `rag_results.json`.

### Experiment 3 - Prompt Chaining
- Processed a phishing incident at NorthBridge Financial Services.
- Extracted 42 targeted employees, 11 credential entries, 3 compromised
  accounts and INR 1.8 million in fraudulent transfers.
- Produced a four-stage report: title, summary, key findings and
  recommendations.
- Offline mode was used for all four steps.

### Experiment 4 - SQL Agent
- Plan -> execute -> answer loop with a schema tool and a read-only SQL tool.
- Answered all four demo questions, including "Which employee has the
  highest salary?" (Sanjay, Finance Manager, 150,000) and the four
  employees with more than 5 years of experience.
- Each record includes SQL, rows, final answer and the full step trace.

### Experiment 5 - Multi-Agent SDR
- Pipeline: `LeadGenerator -> LeadQualifier -> EmailWriter -> SDRSupervisor`.
- 10 leads, 8 qualified, 2 disqualified.
- Tiers: A 5, B 3, D 2. Average score 74.0.
- Pipeline value: $600,000.
- Saved scored leads, generated emails, KPIs and execution trace.

### Experiment 6 - Policy Compliance
- 10 policies, 12 synthetic records, 26 violations.
- Decisions: 2 approve, 5 review, 5 reject.
- Compliance rate: 16.7%.
- Policy hit counts ranged from 1 to 5; the audit includes full evidence
  and remediation text.

### Experiment 7 - Deep Research
- Decomposed the SOC/agentic-AI question into 4 sub-questions.
- Collected 6 unique sources and 18 findings.
- Reflector coverage: 1.00 with no follow-up gaps.
- Synthesised a cited markdown report with references and methodology.

### Experiment 8 - Image Retrieval / Visual QA
- Generated 8 deterministic images and labels.
- Classification accuracy: 100.0% (8/8).
- Answered 6 visual QA questions, including object colour, shape, count,
  image-to-image similarity and dominant colour.
- Fixed the `teal` label during the run and regenerated `images/labels.json`.

### Experiment 9 - Reasoning Benchmark
- 12 questions across 8 categories.
- zero-shot: 25.0% (3/12).
- few-shot: 58.3% (7/12).
- structured: 100.0% (12/12).
- Structured prompting improved every category, including logic and
  sequence where the simpler scaffolds scored 0%.

### Experiment 10 - Fine-Tuning
- Generated 250 training, 80 validation and 250 generic rows.
- Pretrained accuracy: 48.8%; macro-F1 0.461.
- Fine-tuned accuracy: 100.0%; macro-F1 1.000.
- Improvement: +51.2 percentage points.
- Saved checkpoints in `models/` and reports in `results/`.

### Experiment 11 - Model Optimization
- Baseline FP32: 195.5 KB, 100% accuracy.
- INT8 quantized: 49.3 KB, 3.97x compression.
- Structured prune 50%: 97.8 KB, 2.00x compression.
- Structured prune 50% + INT8: 24.7 KB, 7.93x compression.
- All variants retained 100% test accuracy and p50 latency between
  0.016 and 0.019 ms.

### Experiment 12 - Capstone
- Backend tests: `7 passed` (`test_api.py`).
- Frontend build: Vite production bundle built in 987 ms
  (`dist/assets/index-DlED_R0f.css`, `dist/assets/index-gleOorSZ.js`).
- Live server: `http://127.0.0.1:8000`, provider `offline`,
  model `deterministic-rules`.
- Database counts: 12 customers, 6 products, 120 orders, 24 tickets.
- Knowledge base: 10 documents, 30 chunks.
- Web index: 8 documents.
- Compound question returned 12 cancelled orders plus the refund policy,
  agents `["sql", "rag"]`, confidence 0.947, latency 2.81 ms.
- Browser interaction returned a SQL answer, source card and execution trace.

## Verification commands and results

```text
Experiment 12 backend tests:
.......                                                                  [100%]
7 passed, 1 warning (Starlette httpx deprecation)

Experiment 12 frontend build:
vite v5.4.21 building for production...
37 modules transformed.
dist/index.html                 0.58 kB
dist/assets/index-DlED_R0f.css  17.94 kB
dist/assets/index-gleOorSZ.js  156.54 kB
built in 987ms

Experiment 12 API smoke test:
GET  /api/health -> status ok
POST /api/chat   -> agents ["sql", "rag"], confidence 0.947, latency 2.81 ms
```

## Known warnings and notes

- `pytest` emits a Starlette deprecation warning about `httpx` with
  `starlette.testclient`; all tests pass and the warning is harmless.
- Experiments 1-4 default to interactive mode and require `--demo` or
  `--question` for non-interactive execution.
- The root-level `.venv` is Python 3.12 on Windows. Per-experiment
  `.venv` directories from the original repository are Linux/WSL
  environments and were not used.
- `08_visual_qa/images/*` is gitignored; images and `labels.json` are
  regenerated by `main.py`.
- `10_fine_tuning/models/*` and `11_model_optimization/models/*` are
  gitignored; model checkpoints are regenerated by their scripts.
- `12_capstone/backend/data/*.db` is gitignored; the demo database is
  recreated by the backend.

## Git status

All implementation work is present in the working tree. The repository had
one prior local commit (`edd8e2d Add Agentic AI experiments 1-4`); the
remaining experiment work is uncommitted. See `git status --short` for
the current file list before committing.

No push was performed.
