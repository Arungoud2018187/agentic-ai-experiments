"""Lead generation agent.

Loads the seeded lead database and can synthesise additional leads from
deterministic templates when a larger demo batch is requested.
"""

import json
import random
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
LEADS_PATH = BASE_DIR / "data" / "leads.json"

_FIRST_NAMES = ["Ishaan", "Maya", "Leo", "Sara", "Kabir", "Nora", "Aditya", "Zoe"]
_LAST_NAMES = ["Shah", "Iyer", "Martin", "Khan", "Fischer", "Patel", "Silva", "Gupta"]
_COMPANIES = [
    ("SecureLayer", "SaaS", 260),
    ("HealthBridge", "Healthcare", 980),
    ("SwiftPay", "Fintech", 540),
    ("GridWorks", "Energy", 1200),
    ("ShopStack", "Retail", 180),
]
_TITLES = [
    "Head of Security",
    "SOC Manager",
    "VP of Engineering",
    "Risk Manager",
    "IT Director",
]
_PAINS = [
    "alert fatigue",
    "manual audit evidence",
    "cloud misconfiguration",
    "third-party risk",
    "slow incident triage",
]


class LeadGenerator:
    name = "LeadGenerator"

    def __init__(self, seed=42):
        self.random = random.Random(seed)

    def load_leads(self):
        return json.loads(LEADS_PATH.read_text(encoding="utf-8"))

    def generate(self, count=5, start_id=100):
        leads = []
        for offset in range(count):
            first = self.random.choice(_FIRST_NAMES)
            last = self.random.choice(_LAST_NAMES)
            company, industry, employees = self.random.choice(_COMPANIES)
            title = self.random.choice(_TITLES)
            budget = self.random.choice([12000, 24000, 40000, 60000, 85000])
            intent = self.random.randint(45, 95)

            leads.append(
                {
                    "id": f"L{start_id + offset:03d}",
                    "name": f"{first} {last}",
                    "title": title,
                    "company": company,
                    "industry": industry,
                    "employees": employees,
                    "country": self.random.choice(["India", "United States", "Germany"]),
                    "budget_usd": budget,
                    "intent_score": intent,
                    "source": self.random.choice(["webinar", "linkedin", "demo_request"]),
                    "pain_points": self.random.sample(_PAINS, k=2),
                    "email": f"{first.lower()}.{last.lower()}@{company.lower()}.example",
                }
            )
        return leads

    def run(self, count=0):
        leads = self.load_leads()
        if count > len(leads):
            leads.extend(self.generate(count=count - len(leads)))
        return leads[:count] if count else leads
