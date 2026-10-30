import re

from .llm import LLMUnavailable, ask_llm
from .offline_sql import generate_sql_offline


def generate_sql(question: str, schema: str) -> str:

    prompt = f"""
You are an expert Text-to-SQL system.

Convert the user's natural language question into SQLite SQL.

DATABASE SCHEMA:
{schema}

USER QUESTION:
{question}

RULES:
1. Generate ONLY SQL.
2. Do not use markdown.
3. Do not explain anything.
4. Only generate SELECT queries.
5. Never use INSERT, UPDATE, DELETE, DROP, ALTER, CREATE.
6. Use only tables and columns present in the schema.
7. Use SQLite-compatible SQL.

SQL:
"""

    try:
        response = ask_llm(prompt)
        return clean_sql(response)
    except LLMUnavailable:
        # No model server available: use the deterministic translator so
        # the workflow remains fully executable in a lab/offline setting.
        return generate_sql_offline(question, schema)


def clean_sql(response: str) -> str:

    response = response.strip()

    response = re.sub(
        r"```sql",
        "",
        response,
        flags=re.IGNORECASE
    )

    response = re.sub(
        r"```",
        "",
        response
    )

    response = response.strip()

    # Find SELECT statement if model added extra text
    match = re.search(
        r"(SELECT\s+.*?)(?:;|$)",
        response,
        flags=re.IGNORECASE | re.DOTALL
    )

    if match:
        sql = match.group(1).strip()
        return sql

    return response