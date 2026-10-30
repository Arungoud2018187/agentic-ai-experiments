"""Reflector agent.

Checks whether the collected notes cover the plan, identifies weak
sub-questions and proposes follow-up searches.  This is the step that
turns a linear report into an iterative research workflow.
"""


class ReflectorAgent:
    name = "ReflectorAgent"

    def reflect(self, plan, notes, min_sources=3):
        unique_sources = {
            source["id"]
            for note in notes
            for source in note["sources"]
        }

        gaps = []
        for note in notes:
            if len(note["findings"]) < 2 or note["result_count"] == 0:
                gaps.append(note["subquestion"])

        coverage = min(1.0, len(unique_sources) / max(min_sources, 1))
        coverage *= min(1.0, len(notes) / max(len(plan["subquestions"]), 1))

        if len(unique_sources) < min_sources:
            gaps.append("additional independent sources")

        follow_ups = []
        for gap in gaps[:2]:
            if gap.startswith("additional"):
                follow_ups.append(
                    "What independent evidence or case studies support the main findings?"
                )
            else:
                follow_ups.append(f"Find concrete evidence for: {gap}")

        return {
            "coverage_score": round(coverage, 2),
            "unique_sources": len(unique_sources),
            "gaps": gaps,
            "follow_up_queries": follow_ups,
            "sufficient": len(gaps) == 0,
        }
