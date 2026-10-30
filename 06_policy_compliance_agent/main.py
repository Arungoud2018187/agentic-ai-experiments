"""Experiment 6 - Policy Compliance Agent.

Audits synthetic identity/access records against a declarative policy
set, scores risk, and produces an explainable decision per record.

Usage:
    python main.py
    python main.py --details 3
"""

import argparse
import json
from pathlib import Path

from agent.decision import DecisionEngine
from agent.evaluator import ComplianceEvaluator

RESULT_DIR = Path(__file__).resolve().parent / "results"


def _print_audit(results):
    header = f"{'ID':<8}{'Name':<18}{'Department':<14}{'Risk':>5}  {'Violations':>10}  {'Decision':<9}Reason"
    print(header)
    print("-" * 118)
    for item in results:
        decision = item["decision"]["decision"]
        reason = item["decision"]["reason"]
        print(
            f"{item['record_id']:<8}{item['name']:<18}{item['department']:<14}"
            f"{item['risk_score']:>5}  {item['violation_count']:>10}  {decision:<9}{reason[:60]}"
        )


def _print_details(results, limit=3):
    print("\nVIOLATION DETAILS")
    print("-" * 60)
    shown = 0
    for item in results:
        if not item["violations"]:
            continue
        if shown >= limit:
            break
        shown += 1
        print(f"\n{item['record_id']} - {item['name']} ({item['role']})")
        for violation in item["violations"]:
            print(
                f"  [{violation['severity'].upper():<8}] {violation['policy_id']} "
                f"{violation['policy_name']}"
            )
            print(f"    Framework : {violation['framework']}")
            print(f"    Evidence  : {violation['evidence']}")
            print(f"    Fix       : {violation['remediation']}")


def run(details=3, output_path=None):
    print("=" * 60)
    print("             POLICY COMPLIANCE AGENT")
    print("=" * 60)

    evaluator = ComplianceEvaluator()
    decision_engine = DecisionEngine()

    results = []
    for evaluation in evaluator.evaluate_all():
        decision = decision_engine.decide(evaluation)
        results.append({**evaluation, "decision": decision})

    summary = evaluator.summary(results)
    decisions = {
        "APPROVE": sum(1 for item in results if item["decision"]["decision"] == "APPROVE"),
        "REVIEW": sum(1 for item in results if item["decision"]["decision"] == "REVIEW"),
        "REJECT": sum(1 for item in results if item["decision"]["decision"] == "REJECT"),
    }

    print(f"\nPolicies loaded : {len(evaluator.policies)}")
    print(f"Records audited : {summary['records']}")
    print(f"Compliance rate : {summary['compliance_rate']}%")
    print(f"Violations      : {summary['total_violations']}")
    print(f"Decisions       : {decisions}")

    print("\nAUDIT RESULTS")
    print("-" * 60)
    _print_audit(results)
    _print_details(results, limit=details)

    print("\nPOLICY HIT COUNTS")
    print("-" * 60)
    for policy_id, count in summary["policy_hits"].items():
        print(f"{policy_id}: {count}")

    payload = {
        "summary": summary,
        "decisions": decisions,
        "results": results,
    }

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"\nSaved audit report to {output_path}")

    return payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--details", type=int, default=3)
    parser.add_argument(
        "--output",
        default=str(RESULT_DIR / "compliance_audit.json"),
    )
    args = parser.parse_args()
    run(details=args.details, output_path=args.output)


if __name__ == "__main__":
    main()
