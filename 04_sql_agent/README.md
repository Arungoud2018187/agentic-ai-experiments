# Experiment 4 - SQL Agent with Tool Use

## Aim
Build a tool-using agent that plans a database query, executes it through
a tool and turns the rows into a readable answer, while keeping every step
observable in an execution trace.

## Agent loop
```
question
   |
   v
Planning node ---- get_schema tool ----> schema
   |                                      |
   |<-------------------------------------+
   v
generate SQL (LLM or offline planner)
   |
   v
Execution node --- execute_query tool --> read-only SQLite rows
   |                                      (errors are observed, not raised)
   v
Answer node ----> natural-language answer + full step trace
```

`AgentState` carries the question, generated SQL, result, answer, steps
and iteration count between nodes. The execution node catches tool errors
and records them, so the agent can report a failed query instead of
crashing.

## Tools
| Tool | File | Purpose |
|------|------|---------|
| `get_schema` | `tools/schema_tool.py` | Returns tables and columns |
| `execute_query` | `tools/query_tool.py` | Validates and runs read-only SQL |

SQL must start with `SELECT`; write keywords are rejected before the
query reaches SQLite.

## Files
| File | Purpose |
|------|---------|
| `agent/state.py` | Agent state dataclass |
| `agent/graph.py` | Plan -> execute -> answer orchestration |
| `agent/nodes.py` | Planning, execution and answer nodes |
| `agent/llm.py` | Ollama / OpenAI-compatible provider client |
| `agent/sql_fallback.py` | Deterministic SQL planner for offline runs |
| `tools/database_tool.py` | Creates and seeds `data/company.db` |
| `tools/schema_tool.py` | Schema inspection tool |
| `tools/query_tool.py` | Read-only SQL execution tool |
| `main.py` | Interactive and batch CLI |
| `results/sql_agent_results.json` | Captured answers, SQL and traces |

## Run
From this directory:
```bash
python main.py --demo
python main.py --question "Which department has the highest budget?"
python main.py
```

Provider settings are shared with the other experiments:
`LLM_PROVIDER=auto|ollama|openai|offline`, `OLLAMA_URL`, `OLLAMA_MODEL`,
`OPENAI_BASE_URL`, `OPENAI_API_KEY` and `OPENAI_MODEL`.

## Captured results
| Question | Tool result | Final answer |
|----------|-------------|--------------|
| Security department headcount | `3` | "The answer is 3." |
| Total active-project budget | `850000.0` | "The answer is 850000.0." |
| Highest-paid employee | Sanjay, Finance Manager, 150,000 | Named record with role and salary |
| Employees with > 5 years experience | 4 rows | Ranked list of four employees |

Each JSON record contains `question`, `sql`, `rows`, `answer` and `steps`,
including whether the offline planner was used. Console output is in
`results/run_output.txt`.

## Notes
The offline planner is intentionally narrow and explainable. With a model
server the same planning prompt can generate broader SQL, while the
execution and answer nodes remain unchanged.
