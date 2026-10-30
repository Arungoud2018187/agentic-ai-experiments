"""Synthesizer agent.

Turns research notes into a cited markdown report with an executive
summary, thematic findings, risks, recommendations and references.
"""

import re


class SynthesizerAgent:
    name = "SynthesizerAgent"

    def _register_sources(self, notes):
        registry = {}
        order = []

        for note in notes:
            for source in note["sources"]:
                if source["id"] not in registry:
                    registry[source["id"]] = {
                        **source,
                        "label": f"S{len(order) + 1}",
                    }
                    order.append(source["id"])

        return registry, order

    def _cite(self, source_id, registry):
        source = registry.get(source_id)
        return f"[{source['label']}]" if source else ""

    def _confidence(self, reflection, source_count):
        score = reflection["coverage_score"] * 0.6 + min(source_count / 6, 1.0) * 0.4
        if score >= 0.75:
            label = "High"
        elif score >= 0.5:
            label = "Medium"
        else:
            label = "Low"
        return round(score, 2), label

    def synthesize(self, plan, notes, reflection, passes=1):
        registry, order = self._register_sources(notes)
        confidence, confidence_label = self._confidence(reflection, len(order))

        all_findings = []
        seen = set()
        for note in notes:
            for finding in note["findings"]:
                key = finding["text"].lower().strip()
                if key in seen:
                    continue
                seen.add(key)
                all_findings.append(finding)

        lines = [f"# Deep Research Report", "", f"**Question:** {plan['query']}", ""]

        lines += ["## Executive Summary", ""]
        for finding in all_findings[:4]:
            lines.append(
                f"- {finding['text']} {self._cite(finding['source_id'], registry)}"
            )
        lines.append(
            f"\nConfidence: **{confidence_label}** ({confidence:.2f}) based on "
            f"{len(order)} unique sources and {passes} research pass(es)."
        )
        lines.append("")

        lines += ["## Findings by Sub-question", ""]
        for index, note in enumerate(notes, start=1):
            lines.append(f"### {index}. {note['subquestion']}")
            if not note["findings"]:
                lines.append("- No direct evidence was retrieved for this sub-question.")
            for finding in note["findings"]:
                lines.append(
                    f"- {finding['text']} {self._cite(finding['source_id'], registry)}"
                )
            lines.append("")

        risk_findings = [
            finding
            for finding in all_findings
            if re.search(r"risk|threat|attack|injection|failure|limitation|malicious", finding["text"], re.I)
        ]
        lines += ["## Risks and Limitations", ""]
        if risk_findings:
            for finding in risk_findings[:5]:
                lines.append(
                    f"- {finding['text']} {self._cite(finding['source_id'], registry)}"
                )
        else:
            lines.append("- No explicit risk statements were found in the retrieved sources.")
        lines.append("")

        action_findings = [
            finding
            for finding in all_findings
            if re.search(r"should|must|recommend|control|defen|mitigat|allow-list|least privilege", finding["text"], re.I)
        ]
        lines += ["## Recommendations", ""]
        if action_findings:
            for finding in action_findings[:6]:
                lines.append(
                    f"- {finding['text']} {self._cite(finding['source_id'], registry)}"
                )
        else:
            lines.append("- Validate the findings with additional primary sources.")
        lines.append("")

        lines += ["## Evidence Gaps", ""]
        if reflection["gaps"]:
            for gap in reflection["gaps"]:
                lines.append(f"- {gap}")
        else:
            lines.append("- No material gaps were detected in the collected evidence.")
        lines.append("")

        lines += ["## References", ""]
        for source_id in order:
            source = registry[source_id]
            lines.append(
                f"- **[{source['label']}]** {source['title']} - {source['url']} "
                f"({source['source']})"
            )
        lines.append("")

        lines += [
            "## Methodology",
            "",
            f"- Plan: {plan['strategy']}",
            f"- Sub-questions investigated: {len(notes)}",
            f"- Research passes: {passes}",
            f"- Unique sources: {len(order)}",
            f"- Coverage score: {reflection['coverage_score']:.2f}",
            "- Retrieval: lexical search over a curated corpus (offline mode) "
            "or DuckDuckGo plus page extraction (live mode).",
        ]

        return {
            "markdown": "\n".join(lines),
            "metadata": {
                "query": plan["query"],
                "sources": len(order),
                "findings": len(all_findings),
                "confidence": confidence,
                "confidence_label": confidence_label,
                "coverage": reflection["coverage_score"],
                "passes": passes,
                "gaps": reflection["gaps"],
            },
        }
