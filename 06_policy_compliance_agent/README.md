# Experiment 6 - Policy Compliance Agent

## Aim
Audit access/identity records against a declarative policy set, compute
a risk score and produce an explainable APPROVE / REVIEW / REJECT
decision.

## Components
| File | Role |
|------|------|
| `data/policies.json` | 10 policies with conditions, severity, framework and remediation |
| `data/synthetic_data.json` | 12 synthetic employee/contractor/vendor records |
| `rules/rule_engine.py` | Condition evaluator (`eq`, `gt`, `in`, `not_in`, ...) |
| `agent/evaluator.py` | Runs all policies, weights severity, aggregates risk |
| `agent/decision.py` | Thresholds and next-action recommendations |
| `main.py` | CLI audit report |

## Risk model
| Severity | Weight |
|----------|--------|
| critical | 40 |
| high | 25 |
| medium | 12 |
| low | 5 |

Risk score is capped at 100. Any critical violation forces **REJECT**;
otherwise score >= 50 → REJECT, >= 20 → REVIEW, else APPROVE.

## Run
```bash
python main.py
python main.py --details 5
```

## Output
`results/compliance_audit.json` contains the summary, decision counts
and full per-record evidence.
