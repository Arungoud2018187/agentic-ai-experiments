"""Four-step prompt chain: extract -> analyze -> summarize -> report."""

from . import offline
from .llm import LLMUnavailable, ask_llm
from .prompts import STEP_1_PROMPT, STEP_2_PROMPT, STEP_3_PROMPT, STEP_4_PROMPT


def _run_step(prompt, fallback, *args):
    try:
        return ask_llm(prompt), False
    except LLMUnavailable:
        return fallback(*args), True


def extract_information(text):
    prompt = STEP_1_PROMPT.format(text=text)
    return _run_step(prompt, offline.extract_information, text)


def analyze_information(information):
    prompt = STEP_2_PROMPT.format(information=information)
    return _run_step(prompt, offline.analyze_information, information)


def summarize_information(analysis):
    prompt = STEP_3_PROMPT.format(analysis=analysis)
    return _run_step(prompt, offline.summarize_information, analysis)


def generate_final_output(summary, analysis):
    prompt = STEP_4_PROMPT.format(summary=summary, analysis=analysis)
    return _run_step(prompt, offline.generate_final_output, summary, analysis)


def run_chain(text):
    """Execute the chain, falling back per-step if the LLM is unavailable."""

    print("\n[1/4] Extracting information...")
    information, offline_used = extract_information(text)

    print("\n[2/4] Analyzing information...")
    analysis, used = analyze_information(information)
    offline_used = offline_used or used

    print("\n[3/4] Generating summary...")
    summary, used = summarize_information(analysis)
    offline_used = offline_used or used

    print("\n[4/4] Creating final output...")
    final_output, used = generate_final_output(summary, analysis)
    offline_used = offline_used or used

    return {
        "information": information,
        "analysis": analysis,
        "summary": summary,
        "final_output": final_output,
        "offline_mode": offline_used,
    }
