from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentState:

    question: str

    steps: list[str] = field(
        default_factory=list
    )

    sql: str = ""

    result: Any = None

    answer: str = ""

    iteration: int = 0