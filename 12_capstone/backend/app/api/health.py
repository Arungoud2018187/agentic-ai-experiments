"""Health and readiness endpoints."""

from fastapi import APIRouter

from app.agents.supervisor import supervisor
from app.config import settings
from app.models.llm import llm_client
from app.tools import database
from app.tools.retrieval import knowledge_base
from app.tools.web_search import web_search

router = APIRouter(tags=["system"])


@router.get("/health")
def health():
    database_health = database.health()
    llm_health = llm_client.status()
    overall = "ok" if database_health.get("status") == "ready" else "degraded"
    return {
        "status": overall,
        "app": settings.app_name,
        "version": settings.version,
        "llm": llm_health,
        "database": database_health,
        "knowledge_base": {
            "status": "ready" if knowledge_base.count else "empty",
            "documents": knowledge_base.count,
            "chunks": knowledge_base.chunk_count,
        },
        "web_index": web_search.health(),
        "agents": supervisor.describe_agents(),
    }
