"""Experiment 7 - Deep Research Agent Workflow.

Planner -> Researcher -> Reflector -> (follow-up research) -> Synthesizer.

Usage:
    python main.py --demo
    python main.py --query "How can agentic AI improve SOC operations?"
    python main.py --demo --live        # use DuckDuckGo instead of the corpus
"""

import argparse
import json
from pathlib import Path

from agents.planner import PlannerAgent
from agents.reflector import ReflectorAgent
from agents.researcher import ResearcherAgent
from agents.synthesizer import SynthesizerAgent

DEMO_QUERY = (
    "How can agentic AI improve SOC operations while managing prompt injection risk?"
)

RESULT_DIR = Path(__file__).resolve().parent / "results"


def run(query, live=False, max_results=3, output_dir=None):
    print("=" * 60)
    print("             DEEP RESEARCH AGENT")
    print("=" * 60)
    print(f"\nQuestion: {query}")
    print(f"Mode    : {'live web' if live else 'offline corpus'}")

    planner = PlannerAgent()
    researcher = ResearcherAgent(offline=not live)
    reflector = ReflectorAgent()
    synthesizer = SynthesizerAgent()

    plan = planner.plan(query)
    print("\n[PLANNER] Sub-questions:")
    for index, question in enumerate(plan["subquestions"], start=1):
        print(f"  {index}. {question}")

    notes = []
    for question in plan["subquestions"]:
        print(f"\n[RESEARCHER] Searching: {question}")
        note = researcher.research(question, max_results=max_results)
        notes.append(note)
        print(
            f"  -> {len(note['sources'])} sources, {len(note['findings'])} findings"
        )

    reflection = reflector.reflect(plan, notes)
    print(
        f"\n[REFLECTOR] coverage={reflection['coverage_score']:.2f}, "
        f"sources={reflection['unique_sources']}, gaps={len(reflection['gaps'])}"
    )

    passes = 1
    if reflection["follow_up_queries"]:
        passes = 2
        print("\n[REFLECTOR] Running follow-up research:")
        for question in reflection["follow_up_queries"][:2]:
            print(f"  - {question}")
            note = researcher.research(question, max_results=max_results)
            notes.append(note)
            print(
                f"    -> {len(note['sources'])} sources, "
                f"{len(note['findings'])} findings"
            )

        reflection = reflector.reflect(plan, notes)
        print(
            f"\n[REFLECTOR] post-follow-up coverage={reflection['coverage_score']:.2f}, "
            f"gaps={len(reflection['gaps'])}"
        )

    print("\n[SYNTHESIZER] Writing cited report...")
    report = synthesizer.synthesize(plan, notes, reflection, passes=passes)

    print("\n" + "=" * 60)
    print("RESEARCH REPORT")
    print("=" * 60)
    print(report["markdown"])

    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "deep_research_report.md").write_text(
            report["markdown"], encoding="utf-8"
        )
        payload = {
            "query": query,
            "plan": plan,
            "notes": notes,
            "reflection": reflection,
            "metadata": report["metadata"],
            "markdown": report["markdown"],
        }
        (output_dir / "deep_research_results.json").write_text(
            json.dumps(payload, indent=2), encoding="utf-8"
        )
        print(f"\nSaved report to {output_dir / 'deep_research_report.md'}")

    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--query", default=None)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--max-results", type=int, default=3)
    parser.add_argument("--output-dir", default=str(RESULT_DIR))
    args = parser.parse_args()

    query = args.query or DEMO_QUERY
    run(
        query,
        live=args.live,
        max_results=args.max_results,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()
