"""Lead qualification agent.

Scores each lead with a transparent BANT-style rubric:

    seniority     30
    company size  15
    budget        25
    intent        20
    industry fit  10
    ---------------------
    total        100

Tiers: A >= 80, B >= 65, C >= 50, otherwise disqualified.
"""

_SENIORITY = [
    ("chief", 30),
    ("vp", 30),
    ("head", 28),
    ("director", 26),
    ("manager", 22),
    ("lead", 18),
    ("engineer", 10),
    ("analyst", 9),
    ("administrator", 8),
    ("intern", 2),
]

_FIT_INDUSTRIES = {"fintech", "healthcare", "saas", "energy"}


def _seniority_score(title):
    title = title.lower()
    for keyword, score in _SENIORITY:
        if keyword in title:
            return score
    return 8


def _company_score(employees):
    if employees >= 1000:
        return 15
    if employees >= 200:
        return 12
    if employees >= 50:
        return 8
    return 4


def _budget_score(budget):
    if budget >= 75000:
        return 25
    if budget >= 40000:
        return 20
    if budget >= 20000:
        return 13
    if budget >= 10000:
        return 6
    return 2


class LeadQualifier:
    name = "LeadQualifier"

    def score(self, lead):
        breakdown = {
            "seniority": _seniority_score(lead["title"]),
            "company_size": _company_score(lead["employees"]),
            "budget": _budget_score(lead["budget_usd"]),
            "intent": round(lead["intent_score"] / 100 * 20, 1),
            "industry_fit": 10 if lead["industry"].lower() in _FIT_INDUSTRIES else 5,
        }

        total = round(sum(breakdown.values()), 1)

        if total >= 80:
            tier = "A"
        elif total >= 65:
            tier = "B"
        elif total >= 50:
            tier = "C"
        else:
            tier = "D"

        qualified = total >= 65
        reasons = self._reasons(lead, breakdown, total)

        return {
            **lead,
            "score": total,
            "tier": tier,
            "qualified": qualified,
            "score_breakdown": breakdown,
            "qualification_reasons": reasons,
        }

    def _reasons(self, lead, breakdown, total):
        reasons = []
        if breakdown["seniority"] >= 26:
            reasons.append(f"Senior decision maker ({lead['title']})")
        if breakdown["budget"] >= 20:
            reasons.append(f"Budget of ${lead['budget_usd']:,} aligns with the offering")
        if lead["intent_score"] >= 75:
            reasons.append(f"High intent score ({lead['intent_score']}/100)")
        if breakdown["company_size"] >= 12:
            reasons.append(f"Company size ({lead['employees']} employees) fits the ICP")
        if not reasons:
            reasons.append("Limited buying signals in the current profile")

        if total < 65:
            reasons.append("Below the 65-point qualification threshold")
        return reasons

    def run(self, leads):
        scored = [self.score(lead) for lead in leads]
        return sorted(scored, key=lambda item: item["score"], reverse=True)
