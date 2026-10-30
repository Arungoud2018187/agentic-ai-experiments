"""Experiment 5 - Multi-Agent Sales Development Representative (SDR).

A supervisor agent coordinates three specialists:

  1. LeadGenerator  - loads / synthesises leads
  2. LeadQualifier  - scores leads with a transparent BANT-style rubric
  3. EmailWriter    - writes personalised outreach for qualified leads

Usage:
    python main.py --demo
    python main.py --count 15
    python main.py --show-emails
"""

import argparse
import json
from pathlib import Path

from agents.supervisor import SDRSupervisor

RESULT_DIR = Path(__file__).resolve().parent / "results"


def _print_table(leads):
    header = f"{'ID':<6}{'Name':<20}{'Company':<22}{'Title':<28}{'Score':>6}  {'Tier':<5}{'Status'}"
    print(header)
    print("-" * len(header))
    for lead in leads:
        status = "QUALIFIED" if lead["qualified"] else "disqualified"
        print(
            f"{lead['id']:<6}{lead['name']:<20}{lead['company']:<22}"
            f"{lead['title'][:26]:<28}{lead['score']:>6}  {lead['tier']:<5}{status}"
        )


def _print_summary(summary):
    print("\nCAMPAIGN SUMMARY")
    print("-" * 60)
    print(f"Total leads        : {summary['total_leads']}")
    print(f"Qualified          : {summary['qualified_leads']}")
    print(f"Disqualified       : {summary['disqualified_leads']}")
    print(f"Qualification rate : {summary['qualification_rate']}%")
    print(f"Average score      : {summary['average_score']}")
    print(f"Tiers              : {summary['tiers']}")
    print(f"Pipeline value     : ${summary['pipeline_value_usd']:,}")


def run(count=0, show_emails=False, output_path=None):
    print("=" * 60)
    print("             MULTI-AGENT SDR SYSTEM")
    print("=" * 60)

    supervisor = SDRSupervisor()
    report = supervisor.run(count=count)

    print("\nAGENT TRACE")
    print("-" * 60)
    for step in report["trace"]:
        print(f"[{step['step']}] {step['agent']:<16} {step['action']}")

    print("\nSCORED LEADS")
    print("-" * 60)
    _print_table(report["leads"])
    _print_summary(report["summary"])

    if show_emails and report["emails"]:
        print("\nOUTREACH EMAILS")
        print("-" * 60)
        for email in report["emails"]:
            print(f"\nTo      : {email['to']}")
            print(f"Subject : {email['subject']}")
            print(email["body"])

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"\nSaved campaign report to {output_path}")

    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true", help="run the seeded demo")
    parser.add_argument("--count", type=int, default=0, help="number of leads")
    parser.add_argument("--show-emails", action="store_true")
    parser.add_argument(
        "--output",
        default=str(RESULT_DIR / "sdr_campaign_report.json"),
    )
    args = parser.parse_args()

    run(
        count=args.count,
        show_emails=args.show_emails or args.demo,
        output_path=args.output,
    )


if __name__ == "__main__":
    main()
