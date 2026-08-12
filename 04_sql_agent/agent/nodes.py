import json
import requests

from tools.schema_tool import get_schema
from tools.query_tool import execute_query


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen3:8b"


def ask_llm(prompt):

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "think": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 500
            }
        },
        timeout=300
    )

    response.raise_for_status()

    return response.json()["response"].strip()


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

    sql = ask_llm(prompt)

    sql = sql.replace(
        "```sql", ""
    ).replace(
        "```", ""
    ).strip()

    state.sql = sql

    state.steps.append(
        f"Generated SQL: {sql}"
    )

    return state


def execution_node(state):

    result = execute_query(
        state.sql
    )

    state.result = result

    state.steps.append(
        f"SQL Result: {result}"
    )

    return state


def answer_node(state):

    prompt = f"""
You are a database assistant.

USER QUESTION:
{state.question}

SQL QUERY:
{state.sql}

DATABASE RESULT:
{json.dumps(state.result, indent=2)}

Answer the user clearly.

Do not mention internal tools.
Do not invent information.
"""

    state.answer = ask_llm(prompt)

    state.steps.append(
        f"Final Answer: {state.answer}"
    )

    return state