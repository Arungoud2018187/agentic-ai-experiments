"""Chat and agent-discovery endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.agents.supervisor import supervisor

router = APIRouter(tags=["chat"])

EXAMPLES = [
    "What was total revenue in 2025?",
    "Which five customers generated the most revenue?",
    "How many cancelled orders do we have?",
    "What is the refund policy?",
    "Compare NovaDesk pricing with the market and summarize the latest agentic AI trends.",
    "How many open support tickets are there and what is our SLA?",
]


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="Natural-language question")
    session_id: str | None = Field(default=None, max_length=100)
    include_trace: bool = Field(default=True, description="Return tool calls and structured data")


@router.post("/chat")
def chat(payload: ChatRequest):
    try:
        response = supervisor.handle(payload.message)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 - return a stable API error
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {exc}") from exc

    if payload.session_id:
        response["session_id"] = payload.session_id
    if not payload.include_trace:
        response.pop("tool_calls", None)
        response.pop("data", None)
    return response


@router.get("/agents")
def agents():
    return {"agents": supervisor.describe_agents()}


@router.get("/examples")
def examples():
    return {"examples": EXAMPLES}
