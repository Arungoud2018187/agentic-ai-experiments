"""Personalised outreach email writer.

Templates are selected by tier and the lead's stated pain points.  If an
LLM is configured the same input is passed through the model; otherwise
the deterministic template guarantees reproducible lab output.
"""

from textwrap import dedent

_VALUE_BY_PAIN = {
    "alert fatigue": "cut alert noise with risk-ranked detections and automated triage",
    "manual compliance reporting": "automate evidence collection and generate audit-ready reports",
    "manual audit evidence": "collect and map control evidence automatically",
    "fragmented SIEM data": "unify telemetry from endpoint, cloud and identity sources",
    "too many false positives": "prioritise only the incidents that need human attention",
    "slow incident triage": "compress triage from hours to minutes with guided response playbooks",
    "cloud misconfiguration": "continuously detect risky cloud configurations",
    "third-party risk": "score vendor risk with continuous evidence instead of annual questionnaires",
    "regulatory audits": "keep policy mappings current across every audit framework",
    "phishing awareness": "run targeted phishing simulations with measurable coaching",
    "secrets sprawl": "find and rotate exposed credentials across repositories",
    "prompt injection testing": "test LLM applications against prompt injection and data leakage",
    "fraud detection": "combine behavioural signals with transaction risk scoring",
    "policy drift": "monitor policy drift and alert owners before audits",
    "password resets": "reduce helpdesk load with self-service access controls",
}


class EmailWriter:
    name = "EmailWriter"

    def subject(self, lead):
        pain = lead.get("pain_points", ["security operations"])[0]
        return f"Reducing {pain} at {lead['company']}"

    def write(self, lead):
        first_name = lead["name"].split()[0]
        pain = lead.get("pain_points", ["security operations"])[0]
        value = _VALUE_BY_PAIN.get(
            pain,
            "reduce operational risk with an agentic security workflow",
        )

        greeting = f"Hi {first_name},"
        opening = (
            f"I noticed {lead['company']} is investing in {lead['industry'].lower()} "
            f"security and that {pain} is on your radar."
        )
        value_line = (
            f"Our platform helps teams like yours {value}. "
            "It connects to the tools you already use and produces an auditable trail."
        )

        if lead["tier"] == "A":
            proof = (
                "Teams of a similar size have reduced manual review time by about 40% "
                "within the first quarter."
            )
            cta = "Would a 20-minute technical walkthrough next week be useful?"
        elif lead["tier"] == "B":
            proof = (
                "A short pilot is usually enough to measure the reduction in manual work."
            )
            cta = "Would you be open to a 20-minute discovery call?"
        else:
            proof = "I can share a short case study if that is helpful."
            cta = "Would it make sense to stay in touch for a future evaluation?"

        closing = "Best regards,\nGrowvion Security Team"

        body = "\n\n".join([greeting, opening, value_line, proof, cta, closing])

        return {
            "lead_id": lead["id"],
            "to": lead["email"],
            "subject": self.subject(lead),
            "body": body,
            "tier": lead["tier"],
            "personalisation": {
                "pain_point": pain,
                "value_hook": value,
            },
        }

    def run(self, qualified_leads):
        return [self.write(lead) for lead in qualified_leads]
