"""Offline implementations of the four prompt-chain steps.

The functions mirror the prompts in ``prompts.py`` using deterministic
extractive NLP (sentence ranking, cue-word analysis, entity/number
extraction).  This keeps the experiment executable without an LLM server
while preserving the same input/output contract as the prompts.
"""

import re
from collections import Counter

_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "by", "can", "could",
    "did", "do", "does", "for", "from", "had", "has", "have", "he", "her",
    "his", "i", "if", "in", "into", "is", "it", "its", "may", "might", "more",
    "most", "not", "of", "on", "or", "our", "that", "the", "their", "them",
    "then", "there", "these", "they", "this", "to", "was", "were", "which",
    "who", "will", "with", "would", "you", "your", "also", "after", "before",
    "during", "over", "under", "between", "within", "without", "been",
}


def paragraphs(text):
    """Split on blank lines, then unwrap hard line breaks."""

    blocks = re.split(r"\n\s*\n", text)
    return [re.sub(r"\s+", " ", block).strip() for block in blocks if block.strip()]


def split_sentences(text):
    sentences = []
    for block in paragraphs(text):
        sentences.extend(
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", block)
            if sentence.strip()
        )
    return sentences


def _words(text):
    return re.findall(r"[A-Za-z][A-Za-z0-9'-]*", text.lower())


def _content_words(text):
    return [word for word in _words(text) if word not in _STOPWORDS and len(word) > 2]


def _rank_sentences(text, limit, skip_first=False):
    sentences = split_sentences(text)
    if skip_first and len(sentences) > 1:
        sentences = sentences[1:]

    frequencies = Counter(_content_words(" ".join(sentences)))

    scored = []
    for index, sentence in enumerate(sentences):
        if len(sentence.split()) < 5:
            continue
        terms = _content_words(sentence)
        if not terms:
            continue
        score = sum(frequencies[term] for term in terms) / (len(terms) ** 0.5)
        score += 1.0 / (index + 1)
        scored.append((score, sentence))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [sentence for _, sentence in scored[:limit]]


def _extract_entities(text):
    entities = []

    for match in re.findall(r"\b[A-Z][a-zA-Z0-9]+(?:\s+[A-Z][a-zA-Z0-9]+)+\b", text):
        if match not in entities:
            entities.append(match)

    for acronym in re.findall(r"\b[A-Z]{2,}\b", text):
        if acronym not in entities:
            entities.append(acronym)

    for entity in entities:
        if len(entities) >= 10:
            break

    return entities[:10]


def extract_information(text):
    blocks = paragraphs(text)
    topic = blocks[0] if blocks else "Untitled"
    if len(topic.split()) > 14:
        topic = " ".join(topic.split()[:14]) + "..."

    main_points = _rank_sentences(text, 8, skip_first=True)

    facts = [
        sentence
        for sentence in split_sentences(text)
        if re.search(r"\b\d[\d,.]*%?\b|\b(19|20)\d{2}\b", sentence)
    ][:6]

    entities = _extract_entities(" ".join(blocks[1:]) if len(blocks) > 1 else text)
    numbers = list(dict.fromkeys(re.findall(r"\b\d[\d,.]*%?\b", text)))[:10]

    lines = ["TOPIC:", topic, "", "MAIN POINTS:"]
    lines.extend(f"- {point}" for point in (main_points or [topic]))

    lines.extend(["", "IMPORTANT FACTS:"])
    lines.extend(f"- {fact}" for fact in (facts or main_points[:3] or [topic]))

    lines.extend(
        ["", "KEY ENTITIES:", ", ".join(entities) if entities else "None detected"]
    )
    lines.extend(
        ["", "IMPORTANT NUMBERS:", ", ".join(numbers) if numbers else "None detected"]
    )

    return "\n".join(lines)


def _section(information, name):
    """Return the bullet items of a named section."""

    items = []
    current = None
    for line in information.splitlines():
        stripped = line.strip()
        if stripped.endswith(":"):
            current = stripped[:-1].strip().upper()
        elif current == name and stripped.startswith("-"):
            items.append(stripped.lstrip("- ").strip())
    return items


def _matching(sentences, cues):
    return [
        sentence
        for sentence in sentences
        if any(cue in sentence.lower() for cue in cues)
    ]


def analyze_information(information):
    body = _section(information, "MAIN POINTS") + _section(
        information, "IMPORTANT FACTS"
    )
    body = list(dict.fromkeys(body))
    sentences = body or split_sentences(information)

    problems = _matching(
        sentences,
        ["problem", "challenge", "issue", "risk", "threat", "phishing", "attack", "breach", "failure", "gap", "weakness", "compromised"],
    )
    causes = _matching(
        sentences,
        ["because", "due to", "caused by", "root cause", "reason", "result of", "enabled"],
    )
    effects = _matching(
        sentences,
        ["impact", "effect", "caused", "led to", "leads to", "consequence", "affected", "loss", "damage", "delay", "fraudulent", "reputational"],
    )
    actions = _matching(
        sentences,
        ["should", "must", "need to", "recommend", "mitigat", "implement", "deploy"],
    )
    observations = [
        sentence
        for sentence in _rank_sentences("\n".join(sentences), 6)
        if sentence not in actions
    ][:4]

    def block(title, items, fallback):
        picked = list(dict.fromkeys(items))[:4] or fallback
        return [f"{title}:"] + [f"- {item}" for item in picked]

    lines = []
    lines += block(
        "MAIN PROBLEM",
        problems,
        sentences[:1] or ["The text does not state an explicit problem."],
    )
    lines.append("")
    lines += block("CAUSES", causes, ["No explicit causal statements were found."])
    lines.append("")
    lines += block("EFFECTS", effects, ["No explicit effects were stated."])
    lines.append("")
    lines += block("IMPORTANT OBSERVATIONS", observations, ["No observations available."])
    lines.append("")
    lines += block(
        "RECOMMENDED ACTIONS",
        actions,
        ["Validate the findings with the relevant stakeholders and define next steps."],
    )

    return "\n".join(lines)


def summarize_information(analysis):
    problems = _section(analysis, "MAIN PROBLEM")
    causes = _section(analysis, "CAUSES")
    effects = _section(analysis, "EFFECTS")
    observations = _section(analysis, "IMPORTANT OBSERVATIONS")

    candidate_sentences = problems[:1] + causes[:1] + effects[:1]
    if len(candidate_sentences) < 2:
        candidate_sentences += observations[:2]

    if not candidate_sentences:
        candidate_sentences = [
            sentence
            for sentence in split_sentences(analysis)
            if not sentence.endswith(":")
        ][:3]

    summary = " ".join(dict.fromkeys(candidate_sentences))
    if len(summary) > 600:
        summary = summary[:597].rsplit(" ", 1)[0] + "..."

    return summary


def _clean_title(value):
    value = value.strip().lstrip("- ").strip()
    if len(value) > 100:
        value = value[:97].rsplit(" ", 1)[0] + "..."
    return value or "Structured Analysis Report"


def generate_final_output(summary, analysis):
    problems = _section(analysis, "MAIN PROBLEM")
    findings = _section(analysis, "IMPORTANT OBSERVATIONS")
    recommendations = _section(analysis, "RECOMMENDED ACTIONS")

    if not findings:
        findings = problems[:3]

    title = _clean_title(problems[0] if problems else summary.split(".")[0])
    if "phishing" in title.lower():
        title = "Phishing Incident Analysis Report"
    elif title.lower().startswith(("the text does not", "on ", "in ", "the ", "at ")):
        title = "Security Incident Analysis Report"

    lines = [
        "TITLE:",
        title,
        "",
        "SUMMARY:",
        summary,
        "",
        "KEY FINDINGS:",
    ]
    lines.extend(f"- {item}" for item in findings[:3])
    lines.extend(["", "RECOMMENDATIONS:"])
    lines.extend(f"- {item}" for item in recommendations[:3])
    lines.extend(["", "SOURCE INFORMATION:", summary])

    return "\n".join(lines)
