from .llm import ask_llm
from .prompts import (
    STEP_1_PROMPT,
    STEP_2_PROMPT,
    STEP_3_PROMPT,
    STEP_4_PROMPT
)


def extract_information(text):

    prompt = STEP_1_PROMPT.format(
        text=text
    )

    return ask_llm(prompt)


def analyze_information(information):

    prompt = STEP_2_PROMPT.format(
        information=information
    )

    return ask_llm(prompt)


def summarize_information(analysis):

    prompt = STEP_3_PROMPT.format(
        analysis=analysis
    )

    return ask_llm(prompt)


def generate_final_output(
    summary,
    analysis
):

    prompt = STEP_4_PROMPT.format(
        summary=summary,
        analysis=analysis
    )

    return ask_llm(prompt)


def run_chain(text):

    print("\n[1/4] Extracting information...")

    information = extract_information(
        text
    )

    print("\n[2/4] Analyzing information...")

    analysis = analyze_information(
        information
    )

    print("\n[3/4] Generating summary...")

    summary = summarize_information(
        analysis
    )

    print("\n[4/4] Creating final output...")

    final_output = generate_final_output(
        summary,
        analysis
    )

    return {
        "information": information,
        "analysis": analysis,
        "summary": summary,
        "final_output": final_output
    }