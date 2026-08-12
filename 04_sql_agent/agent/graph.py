from .state import AgentState
from .nodes import (
    planning_node,
    execution_node,
    answer_node
)


def run_agent(question):

    state = AgentState(
        question=question
    )

    print("\n[AGENT] Analyzing question...")

    state = planning_node(state)

    print(
        f"[TOOL] SQL generated:\n{state.sql}"
    )

    print("\n[TOOL] Executing SQL...")

    state = execution_node(state)

    print(
        f"[TOOL] Result: {state.result}"
    )

    print("\n[AGENT] Generating answer...")

    state = answer_node(state)

    return state