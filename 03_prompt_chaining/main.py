"""Experiment 3 - Prompt Chaining for Summarization.

A four-stage chain:
  1. extract important information
  2. analyze problems / causes / effects / actions
  3. produce a concise summary
  4. produce a structured final report

Usage
-----
    python main.py                 # interactive (finish with END)
    python main.py --demo          # built-in sample text
    python main.py --file input.txt
"""

import argparse
import json
from pathlib import Path

from src.chain import run_chain

DEMO_TEXT = """Phishing Incident at NorthBridge Financial Services

On 14 March 2026, NorthBridge Financial Services detected a targeted
phishing campaign against 42 employees in its payments division. The
attackers spoofed the internal payroll portal and sent emails asking
staff to re-authenticate to receive a bonus. Eleven employees entered
their credentials, and three accounts were used to approve fraudulent
transfers worth 1.8 million rupees.

The root cause was a combination of weak email authentication, missing
DMARC enforcement, and insufficient security awareness training. Because
the compromised accounts belonged to finance managers, the attackers
could bypass the usual dual-approval control. The incident caused a
delay in salary payments, reputational damage, and an regulatory review.

The security team should enforce DMARC, deploy phishing-resistant MFA,
run quarterly awareness simulations, and add anomaly detection to the
payment approval workflow. The finance department must also review all
transactions made during the 36-hour compromise window.
"""

RESULT_DIR = Path(__file__).resolve().parent / "results"


def print_chain_result(result):
    labels = [
        ("information", "STEP 1 - EXTRACTED INFORMATION"),
        ("analysis", "STEP 2 - ANALYSIS"),
        ("summary", "STEP 3 - SUMMARY"),
        ("final_output", "STEP 4 - FINAL OUTPUT"),
    ]

    for key, label in labels:
        print("\n" + "=" * 60)
        print(label)
        print("=" * 60)
        print(result[key])


def run(text, output_path=None):
    result = run_chain(text)
    print_chain_result(result)

    print(f"\nMode: {'offline fallback' if result['offline_mode'] else 'LLM'}")

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"input": text, **result}
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"Saved JSON result to {output_path}")

    return result


def interactive():
    print("=" * 60)
    print("             PROMPT CHAINING SYSTEM")
    print("=" * 60)
    print("\nEnter text to analyze.")
    print("Type 'END' on a new line when finished.")
    print("Type 'exit' to quit.\n")

    while True:
        lines = []
        while True:
            line = input()
            if line.lower() == "exit":
                return
            if line == "END":
                break
            lines.append(line)

        text = "\n".join(lines).strip()
        if not text:
            print("No text provided.")
            continue

        try:
            run(text)
        except Exception as error:  # noqa: BLE001
            print("\nERROR:")
            print(error)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--file", help="read input text from a file")
    parser.add_argument(
        "--output",
        default=str(RESULT_DIR / "prompt_chain_results.json"),
    )
    args = parser.parse_args()

    if args.file:
        text = Path(args.file).read_text(encoding="utf-8")
        run(text, args.output)
    elif args.demo:
        run(DEMO_TEXT, args.output)
    else:
        interactive()


if __name__ == "__main__":
    main()
