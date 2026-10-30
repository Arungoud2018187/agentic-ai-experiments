"""Supervisor agent for the SDR workflow.

Coordinates three specialist agents:

    LeadGenerator -> LeadQualifier -> EmailWriter

The supervisor owns the workflow, records an execution trace and builds
the final campaign report.
"""

from collections import Counter, defaultdict

from agents.email_writer import EmailWriter
from agents.lead_generator import LeadGenerator
from agents.lead_qualifier import LeadQualifier


class SDRSupervisor:
    name = "SDRSupervisor"

    def __init__(self, seed=42):
        self.generator = LeadGenerator(seed=seed)
        self.qualifier = LeadQualifier()
        self.writer = EmailWriter()

    def run(self, count=0):
        trace = []

        trace.append(
            {
                "step": 1,
                "agent": self.generator.name,
                "action": "load/generate leads",
                "count": count or "all",
            }
        )
        leads = self.generator.run(count)

        trace.append(
            {
                "step": 2,
                "agent": self.qualifier.name,
                "action": "score leads with BANT-style rubric",
                "count": len(leads),
            }
        )
        scored = self.qualifier.run(leads)

        qualified = [lead for lead in scored if lead["qualified"]]
        trace.append(
            {
                "step": 3,
                "agent": self.writer.name,
                "action": "write personalised outreach",
                "count": len(qualified),
            }
        )
        emails = self.writer.run(qualified)

        summary = self._summary(scored, qualified, emails)
        trace.append(
            {
                "step": 4,
                "agent": self.name,
                "action": "aggregate campaign report",
                "status": "complete",
            }
        )

        return {
            "leads": scored,
            "qualified_leads": qualified,
            "emails": emails,
            "summary": summary,
            "trace": trace,
        }

    def _summary(self, scored, qualified, emails):
        tiers = Counter(lead["tier"] for lead in scored)
        industries = Counter(lead["industry"] for lead in scored)

        by_industry = defaultdict(lambda: {"total": 0, "qualified": 0})
        for lead in scored:
            by_industry[lead["industry"]]["total"] += 1
            if lead["qualified"]:
                by_industry[lead["industry"]]["qualified"] += 1

        average_score = (
            round(sum(lead["score"] for lead in scored) / len(scored), 1)
            if scored
            else 0
        )

        return {
            "total_leads": len(scored),
            "qualified_leads": len(qualified),
            "disqualified_leads": len(scored) - len(qualified),
            "emails_written": len(emails),
            "qualification_rate": round(len(qualified) / len(scored) * 100, 1)
            if scored
            else 0,
            "average_score": average_score,
            "tiers": dict(sorted(tiers.items())),
            "by_industry": dict(by_industry),
            "top_lead": qualified[0]["name"] if qualified else None,
            "top_score": qualified[0]["score"] if qualified else 0,
            "pipeline_value_usd": sum(lead["budget_usd"] for lead in qualified),
            "industries": dict(industries),
        }
