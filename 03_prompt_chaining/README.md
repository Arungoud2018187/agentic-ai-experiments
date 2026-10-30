# Experiment 3 - Prompt Chaining

## Aim
Turn a long incident narrative into a structured report by passing the
output of one focused prompt into the next, instead of asking a single
prompt to extract, analyse, summarise and format at once.

## Chain
```
raw text
   |
   v
[1] extract information  -> topic, main points, facts, entities, numbers
   |
   v
[2] analyse information  -> problem, causes, effects, observations, actions
   |
   v
[3] summarise            -> concise factual summary
   |
   v
[4] final report         -> title, summary, key findings, recommendations
```

Each step has a dedicated prompt in `src/prompts.py`. The chain records
whether it used an LLM or the deterministic fallback for every step, so a
mixed run is visible in the output.

## Files
| File | Purpose |
|------|---------|
| `src/prompts.py` | Four step-specific prompts |
| `src/chain.py` | Sequential chain and per-step fallback handling |
| `src/llm.py` | Ollama / OpenAI-compatible provider client |
| `src/offline.py` | Deterministic extractive analysis and report builder |
| `main.py` | Interactive, file and demo CLI |
| `results/prompt_chain_results.json` | Captured step outputs and final report |

## Run
From this directory:
```bash
python main.py --demo
python main.py --file incident.txt
python main.py
```

Provider settings are shared with the other experiments:
`LLM_PROVIDER=auto|ollama|openai|offline`, `OLLAMA_URL`, `OLLAMA_MODEL`,
`OPENAI_BASE_URL`, `OPENAI_API_KEY` and `OPENAI_MODEL`.

## Captured results
The demo processed a phishing incident at NorthBridge Financial Services
through all four steps:

- **Extraction** identified the 14 March 2026 campaign, 42 targeted
  employees, 11 credential entries, 3 compromised accounts and INR 1.8
  million in fraudulent transfers.
- **Analysis** traced the root cause to weak email authentication, missing
  DMARC enforcement and insufficient awareness training, and noted that
  compromised finance-manager accounts bypassed dual approval.
- **Summary** condensed the incident into three factual sentences.
- **Final report** produced a title, summary, three key findings, two
  recommendations and the source section.

The full step-by-step text is in `results/run_output.txt`, and the
structured record is `results/prompt_chain_results.json`.

## Notes
The offline fallback is rule-based and extractive: it selects and
reorganises sentences from the input rather than inventing content. This
keeps the chain deterministic for lab evaluation; with a model server the
same prompts produce generative prose.
