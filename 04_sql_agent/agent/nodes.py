"""Agent nodes: plan -> execute -> answer.

The planning node asks an LLM for SQL and falls back to a deterministic
rule-based translator when no model server is available.  The answer
node always produces a readable response from the query result.
"""

import json
import re

from agent.llm import LLMUnavailable, ask_llm
from agent.sql_fallback import generate_sql_offline
from tools.query_tool import execute_query
from tools.schema_tool import get_schema


def _clean_sql(text):
    text = text.replace("```sql", "").replace("```", "").strip()
    match = re.search(r"(SELECT\s+.*?)(?:;|$)", text, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()
    return text


def planning_node(state):
    schema = get_schema()

    prompt = f"""
You are a SQL database agent.

You have access to these tools:

1. get_schema
2. execute_sql

DATABASE SCHEMA:

{schema}

USER QUESTION:

{state.question}

Decide what SQL query is needed.

Return ONLY valid SQLite SELECT SQL.

Do not use markdown.
Do not explain.
"""

    try:
        sql = _clean_sql(ask_llm(prompt))
        state.steps.append("Planner: LLM generated SQL")
    except LLMUnavailable:
        sql = generate_sql_offline(state.question, schema)
        state.steps.append("Planner: offline rule-based SQL generator")

    state.sql = sql
    state.steps.append(f"Generated SQL: {sql}")

    return state


def execution_node(state):
    try:
        result = execute_query(state.sql)
        state.result = result
        state.steps.append(f"SQL Result: {result}")
    except Exception as error:  # noqa: BLE001 - agent observes tool errors
        state.result = []
        state.steps.append(f"SQL Error: {error}")

    return state


def _offline_answer(question, sql, result):  # noqa: ARG001
    if not result:
        return "No records matched the question."

    if len(result) == 1 and len(result[0]) == 1:
        value = next(iter(result[0].values()))
        return f"The answer is {value}."

    lines = [f"Based on the database, {len(result)} record(s) were found:"]
    for row in result[:10]:
        values = ", ".join(f"{key}: {value}" for key, value in row.items())
        lines.append(f"- {values}")

    if len(result) > 10:
        lines.append(f"... and {len(result) - 10} more.")

    return "\n".join(lines)


def answer_node(state):
    prompt = f"""
You are a database assistant.

USER QUESTION:
{state.question}

SQL QUERY:
{state.sql}

DATABASE RESULT:
{json.dumps(state.result, indent=2, default=str)}

Answer the user clearly.

Do not mention internal tools.
Do not invent information.
"""

    try:
        state.answer = ask_llm(prompt)
        state.steps.append("Answer: LLM generated")
    except LLMUnavailable:
        state.answer = _offline_answer(state.question, state.sql, state.result)
        state.steps.append("Answer: offline formatter")

    state.steps.append(f"Final Answer: {state.answer}")

    return state
