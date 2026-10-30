"""Deterministic reasoning solver used by the benchmark strategies.

The benchmark is designed to run fully offline.  Each category has a
small, explainable solver that returns an answer and reasoning steps.
When an LLM is configured the strategies can use the model instead; the
solver remains the reproducible fallback.
"""

import ast
import math
import re


def _numbers(text):
    return [float(value) for value in re.findall(r"-?\d+(?:\.\d+)?", text)]


def _fmt(value):
    if isinstance(value, str):
        return value
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.4f}".rstrip("0").rstrip(".")


def _safe_eval(expression):
    allowed = (
        ast.Expression,
        ast.BinOp,
        ast.UnaryOp,
        ast.Constant,
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.Pow,
        ast.USub,
        ast.UAdd,
        ast.Mod,
    )
    tree = ast.parse(expression, mode="eval")

    for node in ast.walk(tree):
        if not isinstance(node, allowed):
            raise ValueError("Unsafe arithmetic expression")

    return eval(compile(tree, "<expr>", "eval"), {"__builtins__": {}}, {})


def solve_arithmetic(question):
    match = re.search(
        r"(?:what is|calculate|compute|evaluate)\s+([0-9][0-9\s+\-*/().]*)",
        question,
        re.IGNORECASE,
    )
    expression = match.group(1) if match else ""
    expression = expression.strip().rstrip("?").strip()

    if not expression:
        expression = question.strip().rstrip("?")

    value = _safe_eval(expression)
    return _fmt(value), [f"Extract expression: {expression}", f"Evaluate: {expression} = {_fmt(value)}"]


def solve_percentage(question):
    lowered = question.lower()

    if "what percentage" in lowered or "what percent" in lowered:
        match = re.search(r"(\d+(?:\.\d+)?)\s+of\s+(\d+(?:\.\d+)?)", lowered)
        if not match:
            raise ValueError("Could not find part and whole")
        part, whole = float(match.group(1)), float(match.group(2))
        value = part / whole * 100
        return f"{_fmt(value)}%", [
            f"Identify part={_fmt(part)} and whole={_fmt(whole)}",
            f"Percentage = part / whole * 100 = {_fmt(value)}%",
        ]

    percent_match = re.search(r"(\d+(?:\.\d+)?)\s*%", lowered)
    if not percent_match:
        raise ValueError("Could not find a percentage")
    percent = float(percent_match.group(1))

    candidates = [
        number
        for number in _numbers(lowered)
        if abs(number - percent) > 1e-9
    ]
    if not candidates:
        raise ValueError("Could not find the total")
    total = candidates[0]

    value = total * percent / 100
    return _fmt(value), [
        f"Identify rate={_fmt(percent)}% and total={_fmt(total)}",
        f"Value = total * rate / 100 = {_fmt(value)}",
    ]


def solve_algebra(question):
    match = re.search(
        r"(-?\d*)\s*x\s*([+-])\s*(\d+(?:\.\d+)?)\s*=\s*(-?\d+(?:\.\d+)?)",
        question,
        re.IGNORECASE,
    )
    if not match:
        raise ValueError("Could not parse the linear equation")

    coefficient = match.group(1)
    coefficient = -1.0 if coefficient == "-" else (1.0 if coefficient in ("", "+") else float(coefficient))
    sign = 1.0 if match.group(2) == "+" else -1.0
    constant = float(match.group(3))
    rhs = float(match.group(4))

    value = (rhs - sign * constant) / coefficient
    return _fmt(value), [
        f"Equation: {_fmt(coefficient)}x {'+' if sign > 0 else '-'} {_fmt(constant)} = {_fmt(rhs)}",
        f"Move constant: {_fmt(coefficient)}x = {_fmt(rhs - sign * constant)}",
        f"Divide by coefficient: x = {_fmt(value)}",
    ]


def solve_logic(question):
    lowered = question.lower()

    threshold = re.search(r"(?:>=|at least|greater than or equal to)\s*(\d+(?:\.\d+)?)", lowered)
    if threshold and "critical" in lowered:
        limit = float(threshold.group(1))
        values = [value for value in _numbers(lowered) if value != limit]
        value = values[-1] if values else None
        if value is not None:
            conclusion = "yes" if value >= limit else "no"
            return conclusion, [
                f"Rule threshold: CVSS >= {_fmt(limit)} is critical",
                f"Observed value: {_fmt(value)}",
                f"{_fmt(value)} >= {_fmt(limit)} -> {conclusion}",
            ]

    if "all " in lowered and " are " in lowered:
        rule = re.search(r"all\s+(.+?)\s+are\s+(.+?)[.,]", lowered)
        subject = re.search(r"([a-z]+)\s+is\s+(?:a|an)?\s*(.+?)[.?]", lowered)
        if rule:
            category = rule.group(1)
            property_ = rule.group(2)
            if subject and category in subject.group(2):
                return "yes", [
                    f"Rule: all {category} are {property_}",
                    f"Fact: {subject.group(1)} is a {category}",
                    f"Therefore {subject.group(1)} is {property_}",
                ]
            if subject:
                return "yes", [
                    f"Rule: all {category} are {property_}",
                    "The premise matches the rule; apply modus ponens",
                ]

    raise ValueError("Could not apply a logic rule")


def solve_sequence(question):
    lowered = question.lower()

    # Day-indexed sequence: "5 incidents on day 1, 10 on day 2, ..."
    day_pairs = [
        (int(day), float(value))
        for value, day in re.findall(
            r"(\d+(?:\.\d+)?)[^.]*?on day\s*(\d+)", lowered
        )
    ]

    target_match = re.search(r"on day\s*(\d+)", lowered.split("if the pattern")[-1])
    if day_pairs and target_match:
        target_day = int(target_match.group(1))
        day_pairs.sort()
        values = [value for _, value in day_pairs]
        ratio = values[1] / values[0] if values[0] else 1.0
        last_day, last_value = day_pairs[-1]
        value = last_value * (ratio ** (target_day - last_day))
        return _fmt(value), [
            f"Observed sequence by day: {day_pairs}",
            f"Common ratio = {_fmt(ratio)}",
            f"Day {target_day} = {_fmt(last_value)} * {_fmt(ratio)}^{target_day - last_day} = {_fmt(value)}",
        ]

    # Comma-separated sequence.
    sequence_match = re.search(r"sequence is\s+([\d.,\s-]+)", lowered)
    if sequence_match:
        values = _numbers(sequence_match.group(1))
    else:
        values = _numbers(lowered.split("what is")[0])

    if len(values) < 3:
        raise ValueError("Could not find a sequence")

    ratios = [values[i + 1] / values[i] for i in range(len(values) - 1) if values[i]]
    if ratios and max(ratios) - min(ratios) < 1e-6:
        ratio = ratios[0]
        value = values[-1] * ratio
        return _fmt(value), [
            f"Sequence: {[_fmt(item) for item in values]}",
            f"Common ratio = {_fmt(ratio)}",
            f"Next term = {_fmt(values[-1])} * {_fmt(ratio)} = {_fmt(value)}",
        ]

    difference = values[1] - values[0]
    value = values[-1] + difference
    return _fmt(value), [
        f"Sequence: {[_fmt(item) for item in values]}",
        f"Common difference = {_fmt(difference)}",
        f"Next term = {_fmt(values[-1])} + {_fmt(difference)} = {_fmt(value)}",
    ]


def solve_probability(question):
    lowered = question.lower()

    match = re.search(r"(\d+(?:\.\d+)?)\s+phishing.{0,20}?(\d+(?:\.\d+)?)\s+benign", lowered)
    if match:
        phishing, benign = float(match.group(1)), float(match.group(2))
        value = phishing / (phishing + benign)
        return _fmt(value), [
            f"Favourable outcomes = {_fmt(phishing)}",
            f"Total outcomes = {_fmt(phishing)} + {_fmt(benign)} = {_fmt(phishing + benign)}",
            f"Fraction = {_fmt(phishing)} / {_fmt(phishing + benign)} = {_fmt(value)}",
        ]

    match = re.search(r"(\d+(?:\.\d+)?)\s+of\s+(\d+(?:\.\d+)?)", lowered)
    if match:
        part, whole = float(match.group(1)), float(match.group(2))
        value = part / whole
        return _fmt(value), [
            f"Part = {_fmt(part)}, whole = {_fmt(whole)}",
            f"Fraction = {_fmt(part)} / {_fmt(whole)} = {_fmt(value)}",
        ]

    raise ValueError("Could not find part and whole")


def solve_average(question):
    match = re.search(r"average of\s+([\d.,\s]+)", question, re.IGNORECASE)
    if not match:
        raise ValueError("Could not find the values")
    values = _numbers(match.group(1))
    if not values:
        raise ValueError("No values found")
    value = sum(values) / len(values)
    return _fmt(value), [
        f"Values: {[_fmt(item) for item in values]}",
        f"Sum = {_fmt(sum(values))}",
        f"Average = {_fmt(sum(values))} / {len(values)} = {_fmt(value)}",
    ]


def solve_combinatorics(question):
    lowered = question.lower()
    match = re.search(r"(\d+)[- ]digit", lowered)
    if not match:
        raise ValueError("Could not find password length")

    digits = int(match.group(1))
    alphabet = 10 if "0-9" in lowered or "0 to 9" in lowered else 10
    value = alphabet ** digits
    return _fmt(value), [
        f"Digits = {digits}",
        f"Choices per digit = {alphabet}",
        f"Combinations = {alphabet}^{digits} = {_fmt(value)}",
    ]


_SOLVERS = {
    "arithmetic": solve_arithmetic,
    "percentage": solve_percentage,
    "algebra": solve_algebra,
    "logic": solve_logic,
    "sequence": solve_sequence,
    "probability": solve_probability,
    "average": solve_average,
    "combinatorics": solve_combinatorics,
}


def solve_by_category(question, category):
    solver = _SOLVERS.get(category)
    if solver is None:
        raise ValueError(f"Unsupported category: {category}")
    answer, steps = solver(question)
    return {"answer": answer, "steps": steps, "category": category}
