# Experiment 7 - Deep Research Agent Workflow

## Aim
Build an iterative research agent that plans a question, gathers evidence
from multiple sources, reflects on coverage gaps, performs follow-up
research and synthesises a cited report.

## Agents
| Agent | File | Role |
|-------|------|------|
| `PlannerAgent` | `agents/planner.py` | Decomposes the question into sub-questions |
| `ResearcherAgent` | `agents/researcher.py` | Searches, reads sources, extracts findings |
| `ReflectorAgent` | `agents/reflector.py` | Measures coverage and proposes follow-ups |
| `SynthesizerAgent` | `agents/synthesizer.py` | Produces the cited markdown report |

## Workflow
```
Question -> Planner -> Researcher (per sub-question) -> Reflector
                              ^                           |
                              |------ follow-up ----------|
                                                          v
                                                   Synthesizer -> report
```

## Tools
- `tools/web_search.py` - DuckDuckGo HTML search in live mode; curated
  corpus lexical search in offline mode.
- `tools/page_reader.py` - BeautifulSoup page extraction; local corpus
  documents for the offline demo.

## Run
```bash
python main.py --demo
python main.py --query "What are the risks of prompt injection in AI agents?"
python main.py --demo --live
```

## Output
- `results/deep_research_report.md` - cited report
- `results/deep_research_results.json` - plan, notes, reflection and metadata

## Notes
Offline mode is deterministic and does not require network access,
which is useful for lab demonstrations and repeatable evaluation.
