"""Experiment 1 - End-to-end Text-to-SQL workflow.

Usage
-----
Interactive (default)::

    python main.py

Batch / lab execution::

    python main.py --demo
    python main.py --question "How many employees are there?" --question "..."

The script initialises a SQLite database, reads its schema, asks the LLM
(or the offline rule-based fallback) for SQL, validates it as read-only,
executes it and prints the rows.
"""

import argparse
import json
from pathlib import Path

from src.database import initialize_database
from src.executor import execute_sql
from src.schema import get_database_schema
from src.sql_generator import generate_sql

DEMO_QUESTIONS = [
    "How many employees are there in each department?",
    "What is the average salary by department?",
    "Which employees earn more than 100000?",
    "List all active projects with their department names.",
    "Who has the most experience?",
]

RESULT_DIR = Path(__file__).resolve().parent / "results"


def answer_question(question, schema):
    sql = generate_sql(question, schema)
    rows = execute_sql(sql)
    return sql, rows


def print_result(question, sql, rows):
    print("\nQuestion:")
    print(question)
    print("\nGenerated SQL:")
    print("-" * 60)
    print(sql)
    print("\nResults:")
    print("-" * 60)
    if not rows:
        print("No results found.")
    else:
        for row in rows:
            print(row)


def run_batch(questions, output_path=None):
    initialize_database()
    schema = get_database_schema()

    print("=" * 60)
    print("        TEXT-TO-SQL LLM SYSTEM")
    print("=" * 60)
    print("\nDatabase Schema:")
    print("-" * 60)
    print(schema)

    records = []
    for question in questions:
        try:
            sql, rows = answer_question(question, schema)
            print_result(question, sql, rows)
            records.append(
                {"question": question, "sql": sql, "rows": rows, "error": None}
            )
        except Exception as error:  # noqa: BLE001 - CLI reporting
            print(f"\nQuestion: {question}\nERROR: {error}")
            records.append(
                {"question": question, "sql": None, "rows": [], "error": str(error)}
            )

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(records, indent=2, default=str), encoding="utf-8"
        )
        print(f"\nSaved JSON results to {output_path}")

    return records


def interactive():
    initialize_database()
    schema = get_database_schema()

    print("=" * 60)
    print("        TEXT-TO-SQL LLM SYSTEM")
    print("=" * 60)
    print("\nDatabase Schema:")
    print("-" * 60)
    print(schema)
    print("\nType 'exit' to quit.")

    while True:
        question = input("\nAsk a database question: ").strip()
        if question.lower() == "exit":
            print("Exiting...")
            break
        if not question:
            continue
        try:
            print("\nGenerating SQL...")
            sql, rows = answer_question(question, schema)
            print_result(question, sql, rows)
        except Exception as error:  # noqa: BLE001
            print("\nERROR:")
            print(error)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--demo",
        action="store_true",
        help="run the built-in demonstration questions",
    )
    parser.add_argument(
        "--question",
        action="append",
        default=[],
        help="question to answer (repeatable)",
    )
    parser.add_argument(
        "--output",
        default=str(RESULT_DIR / "text_to_sql_results.json"),
        help="path for the JSON result file",
    )
    args = parser.parse_args()

    if args.demo or args.question:
        run_batch(args.question or DEMO_QUESTIONS, args.output)
    else:
        interactive()


if __name__ == "__main__":
    main()
