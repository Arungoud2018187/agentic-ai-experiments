# Experiment 5 - Multi-Agent SDR System

## Aim
Build a supervisor-driven multi-agent sales development pipeline that
generates leads, qualifies them and writes personalised outreach.

## Agents
| Agent | File | Responsibility |
|-------|------|----------------|
| `SDRSupervisor` | `agents/supervisor.py` | Orchestrates the workflow, records trace, aggregates KPIs |
| `LeadGenerator` | `agents/lead_generator.py` | Loads seeded leads / synthesises deterministic leads |
| `LeadQualifier` | `agents/lead_qualifier.py` | BANT-style scoring, tiers A-D, qualification reasons |
| `EmailWriter` | `agents/email_writer.py` | Personalised subject + body based on pain point and tier |

## Workflow
```
LeadGenerator -> LeadQualifier -> EmailWriter -> Campaign report
       |               |                |
   raw leads       score 0-100      qualified only
                   tiers A-D        personalised copy
```

## Qualification rubric
| Signal | Points |
|--------|--------|
| Seniority | 0-30 |
| Company size | 4-15 |
| Budget | 2-25 |
| Intent score | 0-20 |
| Industry fit | 5-10 |

Tiers: **A** >= 80, **B** >= 65, **C** >= 50, **D** < 50.
Only leads with a score >= 65 receive outreach.

## Run
```bash
python main.py --demo
python main.py --count 15 --show-emails
```

## Output
`results/sdr_campaign_report.json` contains scored leads, qualified
leads, generated emails, summary KPIs and the agent execution trace.
