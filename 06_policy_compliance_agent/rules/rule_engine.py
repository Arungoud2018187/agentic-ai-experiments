"""Declarative rule engine.

Each policy is a list of conditions that must all match for a violation
to be recorded.  Supported operators: eq, ne, gt, gte, lt, lte, in,
not_in, exists, truthy, falsy.
"""


class RuleError(ValueError):
    pass


def _get(record, field):
    if field not in record:
        raise RuleError(f"Record is missing field '{field}'")
    return record[field]


def _compare(actual, operator, expected):
    if operator == "eq":
        return actual == expected
    if operator == "ne":
        return actual != expected
    if operator == "gt":
        return actual > expected
    if operator == "gte":
        return actual >= expected
    if operator == "lt":
        return actual < expected
    if operator == "lte":
        return actual <= expected
    if operator == "in":
        return actual in expected
    if operator == "not_in":
        return actual not in expected
    if operator == "exists":
        return actual is not None
    if operator == "truthy":
        return bool(actual)
    if operator == "falsy":
        return not bool(actual)
    raise RuleError(f"Unsupported operator '{operator}'")


def check_condition(record, condition):
    actual = _get(record, condition["field"])
    return _compare(actual, condition["op"], condition.get("value"))


def evaluate_policy(record, policy):
    """Return a violation dict if every condition matches, else None."""

    matched = all(check_condition(record, condition) for condition in policy["conditions"])
    if not matched:
        return None

    return {
        "policy_id": policy["id"],
        "policy_name": policy["name"],
        "severity": policy["severity"],
        "framework": policy["framework"],
        "description": policy["description"],
        "remediation": policy["remediation"],
        "evidence": [
            {
                "field": condition["field"],
                "actual": record.get(condition["field"]),
                "expected": f"{condition['op']} {condition.get('value')}",
            }
            for condition in policy["conditions"]
        ],
    }


class RuleEngine:
    def __init__(self, policies):
        self.policies = policies

    def evaluate(self, record):
        violations = []
        for policy in self.policies:
            violation = evaluate_policy(record, policy)
            if violation:
                violations.append(violation)
        return violations
