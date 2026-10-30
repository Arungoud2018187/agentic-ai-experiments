"""Compliance evaluator.

Runs the rule engine over every record, computes a weighted risk score
and groups violations by severity.
"""

import json
from collections import Counter
from pathlib import Path

from rules.rule_engine import RuleEngine

BASE_DIR = Path(__file__).resolve().parent.parent
POLICY_PATH = BASE_DIR / "data" / "policies.json"
DATA_PATH = BASE_DIR / "data" / "synthetic_data.json"

SEVERITY_WEIGHTS = {
    "critical": 40,
    "high": 25,
    "medium": 12,
    "low": 5,
}


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


class ComplianceEvaluator:
    def __init__(self, policies=None, records=None):
        self.policies = policies or load_json(POLICY_PATH)
        self.records = records or load_json(DATA_PATH)
        self.engine = RuleEngine(self.policies)

    def evaluate_record(self, record):
        violations = self.engine.evaluate(record)
        severity_counts = Counter(item["severity"] for item in violations)

        risk_score = min(
            100,
            sum(SEVERITY_WEIGHTS.get(item["severity"], 0) for item in violations),
        )

        return {
            "record_id": record["id"],
            "name": record["name"],
            "department": record["department"],
            "role": record["role"],
            "violations": violations,
            "violation_count": len(violations),
            "severity_counts": dict(severity_counts),
            "risk_score": risk_score,
            "compliant": not violations,
        }

    def evaluate_all(self):
        return [self.evaluate_record(record) for record in self.records]

    def summary(self, evaluations):
        total = len(evaluations)
        compliant = sum(1 for item in evaluations if item["compliant"])
        decision_ready = Counter()

        for item in evaluations:
            if any(v["severity"] == "critical" for v in item["violations"]):
                decision_ready["REJECT"] += 1
            elif item["risk_score"] >= 50:
                decision_ready["REJECT"] += 1
            elif item["violations"] or item["risk_score"] >= 20:
                decision_ready["REVIEW"] += 1
            else:
                decision_ready["APPROVE"] += 1

        policy_hits = Counter()
        for item in evaluations:
            for violation in item["violations"]:
                policy_hits[violation["policy_id"]] += 1

        return {
            "records": total,
            "compliant_records": compliant,
            "non_compliant_records": total - compliant,
            "compliance_rate": round(compliant / total * 100, 1) if total else 0,
            "total_violations": sum(item["violation_count"] for item in evaluations),
            "decision_counts": dict(decision_ready),
            "policy_hits": dict(sorted(policy_hits.items())),
            "average_risk_score": round(
                sum(item["risk_score"] for item in evaluations) / total, 1
            )
            if total
            else 0,
        }
