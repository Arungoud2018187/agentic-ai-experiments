"""Decision agent.

Maps evaluated evidence to one of three outcomes and explains why.
"""


class DecisionEngine:
    def decide(self, evaluation):
        violations = evaluation["violations"]
        score = evaluation["risk_score"]

        critical = [item for item in violations if item["severity"] == "critical"]
        high = [item for item in violations if item["severity"] == "high"]

        if critical:
            decision = "REJECT"
            reason = (
                f"{len(critical)} critical violation(s) require immediate remediation: "
                + ", ".join(item["policy_id"] for item in critical)
            )
        elif score >= 50:
            decision = "REJECT"
            reason = (
                f"Risk score {score}/100 exceeds the rejection threshold of 50 "
                f"({len(high)} high-severity violation(s))."
            )
        elif score >= 20 or violations:
            decision = "REVIEW"
            reason = (
                f"Risk score {score}/100 and {len(violations)} policy violation(s) "
                "require manual review before access continues."
            )
        else:
            decision = "APPROVE"
            reason = "No policy violations were detected; the record is compliant."

        next_action = self._next_action(decision, violations)

        return {
            "decision": decision,
            "reason": reason,
            "risk_score": score,
            "next_action": next_action,
            "remediation": [item["remediation"] for item in violations],
        }

    def _next_action(self, decision, violations):
        if decision == "APPROVE":
            return "No action required. Re-audit at the next scheduled review."

        if any(item["severity"] == "critical" for item in violations):
            return "Suspend access, open a P1 remediation ticket and notify the CISO."

        if decision == "REJECT":
            return "Revoke elevated access and complete remediation before re-evaluation."

        return "Assign remediation owners and re-run the audit within 7 days."
