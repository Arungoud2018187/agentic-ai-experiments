"""Experiment 4 - SQL Agent with Tool Use.

The agent follows a plan -> execute -> answer loop and uses two tools:
``get_schema`` (inspect the database) and ``execute_query`` (run a
read-only SELECT).  It works with a local LLM or with the deterministic
offline planner.

Usage:
    python main.py
    python main.py --demo
    python main.py --question "Which department has the highest budget?"
"""

import argparse
import json
from pathlib import Path

from agent.graph import run_agent
from tools.database_tool import initialize_database
from tools.schema_tool import get_schema

DEMO_QUESTIONS = [
    "How many employees work in the Security department?",
    "What is the total budget of active projects?",
    "Which employee has the highest salary?",
    "List employees with more than 5 years of experience.",
]

RESULT_DIR = Path(__file__).resolve().parent / "results"


def answer_question(question):
    state = run_agent(question)

    print("\n" + "=" * 60)
    print("FINAL ANSWER")
    print("=" * 60)
    print(state.answer)

    return {
        "question": question,
        "sql": state.sql,
        "rows": state.result,
        "answer": state.answer,
        "steps": state.steps,
    }


def run_batch(questions, output_path=None):
    initialize_database()

    print("=" * 60)
    print("           SQL AGENT WITH TOOL USE")
    print("=" * 60)
    print("\nDatabase initialized.")
    print("\nAvailable schema:")
    print("-" * 60)
    print(get_schema())

    records = []
    for question in questions:
        print("\n" + "#" * 60)
        print(f"QUESTION: {question}")
        try:
            records.append(answer_question(question))
        except Exception as error:  # noqa: BLE001 - CLI reporting
            print(f"\nAGENT ERROR: {error}")
            records.append(
                {"question": question, "sql": None, "rows": [], "answer": None, "error": str(error)}
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

    print("=" * 60)
    print("           SQL AGENT WITH TOOL USE")
    print("=" * 60)
    print("\nDatabase initialized.")
    print("\nAvailable schema:")
    print("-" * 60)
    print(get_schema())
    print("\nType 'exit' to quit.")

    while True:
        question = input("\nAsk the SQL Agent: ").strip()
        if question.lower() == "exit":
            print("Exiting...")
            break
        if not question:
            continue
        try:
            answer_question(question)
        except Exception as error:  # noqa: BLE001
            print("\nAGENT ERROR:")
            print(error)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--question", action="append", default=[])
    parser.add_argument(
        "--output",
        default=str(RESULT_DIR / "sql_agent_results.json"),
    )
    args = parser.parse_args()

    if args.demo or args.question:
        run_batch(args.question or DEMO_QUESTIONS, args.output)
    else:
        interactive()


if __name__ == "__main__":
    main()
