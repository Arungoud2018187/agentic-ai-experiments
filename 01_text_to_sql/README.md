# Experiment 1 - Text-to-SQL LLM System

## Aim
Translate natural-language questions into read-only SQLite queries,
execute them against a seeded company database and return the resulting
rows with the generated SQL.

## Architecture
```
question
   |
   v
schema introspection -> prompt builder -> LLM provider
   |                                      (Ollama / OpenAI-compatible)
   |                                            |
   |                                            v
   +-------------------------------> SQL cleanup + SELECT-only validation
                                                |
                                                v
                                         SQLite executor
                                                |
                                                v
                                      rows + generated SQL
```

The prompt contains the live database schema and strict rules: return only
SQLite `SELECT` statements, no markdown, no explanations and no writes.
If no model server is reachable, a deterministic rule-based translator
covers the lab question shapes (counts, aggregations, filters, joins,
sorting and limits) so the experiment always runs offline.

## Files
| File | Purpose |
|------|---------|
| `src/database.py` | Creates and seeds `data/company.db` |
| `src/schema.py` | Reads tables, columns and types for the prompt |
| `src/sql_generator.py` | Prompt construction, SQL cleanup, LLM/offline routing |
| `src/offline_sql.py` | Deterministic natural-language to SQL fallback |
| `src/llm.py` | Ollama / OpenAI-compatible provider client |
| `src/executor.py` | Blocks non-SELECT SQL and executes queries |
| `main.py` | Interactive and batch CLI |
| `data/company.db` | Seeded SQLite database |
| `results/text_to_sql_results.json` | Captured questions, SQL and rows |

## Database
| Table | Columns |
|-------|---------|
| `departments` | id, name, location |
| `employees` | id, name, age, department_id, position, salary, experience |
| `projects` | id, name, department_id, budget, status |

## Run
From this directory:
```bash
python main.py --demo
python main.py --question "How many employees are there in each department?"
python main.py
```

Optional model server:
```bash
ollama pull qwen3:8b
ollama serve
```

Provider settings:
| Variable | Default | Meaning |
|----------|---------|---------|
| `LLM_PROVIDER` | `auto` | `auto`, `ollama`, `openai` or `offline` |
| `OLLAMA_URL` | `http://localhost:11434/api/generate` | Ollama generate endpoint |
| `OLLAMA_MODEL` | `qwen3:8b` | Ollama model |
| `OPENAI_BASE_URL` | `http://localhost:1234/v1` | OpenAI-compatible base URL |
| `OPENAI_API_KEY` | empty | Optional bearer token |
| `OPENAI_MODEL` | `local-model` | OpenAI-compatible model name |

`auto` tries Ollama, then the OpenAI-compatible endpoint, then the
offline translator.

## Captured results
`python main.py --demo` answered all five demo questions:

| Question | Result |
|----------|--------|
| Employees per department | Engineering 3, Security 3, Marketing 2, Finance 2 |
| Average salary by department | Finance 127,500; Security 106,666.67; Engineering 90,000; Marketing 90,000 |
| Employees earning > 100,000 | 5 employees, highest Sanjay at 150,000 |
| Active projects with departments | AI Platform (Engineering, 500,000), SOC Automation (Security, 350,000) |
| Most experienced employee | Sanjay, Finance Manager, 12 years |

Generated SQL is printed in `results/run_output.txt`; the machine-readable
record is `results/text_to_sql_results.json`.

## Safety
Only statements beginning with `SELECT` are accepted, and write keywords
(`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`, `REPLACE`,
`TRUNCATE`, `ATTACH`, `DETACH`) are rejected before execution.
