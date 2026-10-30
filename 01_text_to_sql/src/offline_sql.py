"""Deterministic natural-language to SQLite-SQL translator.

This module is the offline fallback for the LLM in experiment 1.  It
covers the question shapes used by the lab demo (counts, aggregations,
filters, sorting and joins) using a small set of regular expressions.
It is intentionally simple, explainable and dependency free.
"""

import re


def _limit(question: str, default: int = 10) -> int:
    match = re.search(r"\b(?:top|first|bottom)\s+(\d+)\b", question)
    if match:
        return max(1, int(match.group(1)))
    match = re.search(r"\b(\d+)\s+(?:employees|people|projects|rows)\b", question)
    if match:
        return max(1, int(match.group(1)))
    return default


def _number(question: str, keywords: str):
    match = re.search(
        rf"{keywords}[^\d]{{0,30}}(\d[\d,]*(?:\.\d+)?)",
        question,
    )
    if not match:
        return None
    return float(match.group(1).replace(",", ""))


def _department(question: str) -> str | None:
    known = {
        "engineering": "Engineering",
        "security": "Security",
        "marketing": "Marketing",
        "finance": "Finance",
    }
    for key, value in known.items():
        if key in question:
            return value
    return None


def _status(question: str) -> str | None:
    for status in ("active", "completed", "pending"):
        if status in question:
            return status.capitalize()
    return None


def generate_sql_offline(question: str, schema: str = "") -> str:  # noqa: ARG001
    """Translate ``question`` into a safe SQLite SELECT statement."""

    q = " ".join(question.lower().split())

    # ---------------------------------------------------------------
    # Projects
    # ---------------------------------------------------------------
    if "project" in q:
        status = _status(q)

        if "total" in q and "budget" in q:
            sql = "SELECT SUM(budget) AS total_budget FROM projects"
            if status:
                sql += f" WHERE status = '{status}'"
            return sql

        if "average" in q and "budget" in q:
            return (
                "SELECT AVG(budget) AS average_budget FROM projects"
            )

        if "department" in q or "which team" in q:
            sql = (
                "SELECT p.name AS project, d.name AS department, "
                "p.budget, p.status "
                "FROM projects p "
                "JOIN departments d ON d.id = p.department_id"
            )
            if status:
                sql += f" WHERE p.status = '{status}'"
            return sql + " ORDER BY p.budget DESC"

        if "highest" in q or "largest" in q or "most expensive" in q:
            return (
                "SELECT name, budget, status FROM projects "
                "ORDER BY budget DESC LIMIT 1"
            )

        sql = "SELECT name, budget, status FROM projects"
        if status:
            sql += f" WHERE status = '{status}'"
        return sql + " ORDER BY budget DESC"

    # ---------------------------------------------------------------
    # Departments
    # ---------------------------------------------------------------
    if "department" in q and "employee" not in q and "salary" not in q:
        if "location" in q:
            return "SELECT name, location FROM departments ORDER BY name"
        return "SELECT id, name, location FROM departments ORDER BY id"

    # ---------------------------------------------------------------
    # Employees - aggregates
    # ---------------------------------------------------------------
    if re.search(r"\bhow many\b|\bcount\b|\bnumber of\b", q) and "employee" in q:
        department = _department(q)
        if department and not any(word in q for word in ("each", "per", "every")):
            return (
                "SELECT COUNT(*) AS employee_count "
                "FROM employees e "
                "JOIN departments d ON d.id = e.department_id "
                f"WHERE d.name = '{department}'"
            )

        if "department" in q or "each" in q or "per" in q:
            return (
                "SELECT d.name AS department, COUNT(e.id) AS employee_count "
                "FROM departments d "
                "LEFT JOIN employees e ON e.department_id = d.id "
                "GROUP BY d.id, d.name "
                "ORDER BY employee_count DESC"
            )
        return "SELECT COUNT(*) AS employee_count FROM employees"

    if "average" in q and "salary" in q:
        if "department" in q or "each" in q or "per" in q:
            return (
                "SELECT d.name AS department, "
                "ROUND(AVG(e.salary), 2) AS average_salary "
                "FROM employees e "
                "JOIN departments d ON d.id = e.department_id "
                "GROUP BY d.id, d.name "
                "ORDER BY average_salary DESC"
            )
        return "SELECT ROUND(AVG(salary), 2) AS average_salary FROM employees"

    if ("total" in q or "sum" in q) and "salary" in q:
        return "SELECT SUM(salary) AS total_salary FROM employees"

    if ("highest" in q or "maximum" in q or "max" in q) and "salary" in q:
        if "department" in q:
            return (
                "SELECT d.name AS department, MAX(e.salary) AS highest_salary "
                "FROM employees e "
                "JOIN departments d ON d.id = e.department_id "
                "GROUP BY d.id, d.name "
                "ORDER BY highest_salary DESC"
            )
        return (
            "SELECT name, position, salary FROM employees "
            "ORDER BY salary DESC LIMIT 1"
        )

    if ("lowest" in q or "minimum" in q or "min" in q) and "salary" in q:
        return (
            "SELECT name, position, salary FROM employees "
            "ORDER BY salary ASC LIMIT 1"
        )

    # ---------------------------------------------------------------
    # Employees - filters / listings
    # ---------------------------------------------------------------
    department = _department(q)

    if "experience" in q:
        value = _number(q, r"(?:more than|greater than|over|above|at least|>)")
        if value is not None:
            operator = ">=" if "at least" in q else ">"
            sql = (
                "SELECT name, position, experience, salary FROM employees "
                f"WHERE experience {operator} {int(value)} "
                "ORDER BY experience DESC"
            )
        elif any(word in q for word in ("most", "highest", "maximum", "max")):
            sql = (
                "SELECT name, position, experience FROM employees "
                "ORDER BY experience DESC LIMIT 1"
            )
        else:
            sql = (
                "SELECT name, position, experience FROM employees "
                "ORDER BY experience DESC"
            )
        if department:
            sql = sql.replace(
                "WHERE",
                f"WHERE department_id = (SELECT id FROM departments WHERE name = '{department}') AND",
            )
        return sql

    if ("salary" in q or "earn" in q or "paid" in q) and re.search(r"\d", q):
        value = _number(q, r"(?:more than|greater than|over|above|at least|less than|below|under|>)")
        if value is not None:
            if any(word in q for word in ("less", "below", "under")):
                operator = "<"
            elif "at least" in q:
                operator = ">="
            else:
                operator = ">"

            sql = (
                "SELECT e.name, d.name AS department, e.position, e.salary "
                "FROM employees e "
                "JOIN departments d ON d.id = e.department_id "
                f"WHERE e.salary {operator} {value:g} "
                "ORDER BY e.salary DESC"
            )
            if department:
                sql += f" AND d.name = '{department}'"
            return sql

    if "department" in q and department:
        return (
            "SELECT e.name, e.position, e.salary, e.experience "
            "FROM employees e "
            "JOIN departments d ON d.id = e.department_id "
            f"WHERE d.name = '{department}' "
            "ORDER BY e.salary DESC"
        )

    if "location" in q:
        # e.g. employees in Hyderabad
        for city in ("hyderabad", "bangalore", "mumbai", "delhi"):
            if city in q:
                return (
                    "SELECT e.name, d.name AS department, d.location "
                    "FROM employees e "
                    "JOIN departments d ON d.id = e.department_id "
                    f"WHERE d.location = '{city.capitalize()}' "
                    "ORDER BY e.name"
                )

    if "top" in q and "salary" in q:
        return (
            "SELECT name, position, salary FROM employees "
            f"ORDER BY salary DESC LIMIT {_limit(q)}"
        )

    if "manager" in q:
        return (
            "SELECT name, position, salary FROM employees "
            "WHERE position LIKE '%Manager%' ORDER BY salary DESC"
        )

    if "security" in q:
        return (
            "SELECT e.name, e.position, e.salary, d.name AS department "
            "FROM employees e JOIN departments d ON d.id = e.department_id "
            "WHERE d.name = 'Security' ORDER BY e.salary DESC"
        )

    if "employee" in q or "who" in q or "name" in q:
        sql = (
            "SELECT name, position, salary, experience FROM employees "
            "ORDER BY salary DESC"
        )
        return sql + f" LIMIT {_limit(q)}"

    # Last-resort readable sample instead of an invalid query.
    return "SELECT name, position, salary FROM employees ORDER BY salary DESC LIMIT 5"
