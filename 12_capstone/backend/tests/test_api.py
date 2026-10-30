"""API tests for the capstone multi-agent assistant."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"]["counts"]["orders"] > 0
    assert body["knowledge_base"]["chunks"] > 0
    assert len(body["agents"]) == 3


def test_agents(client):
    response = client.get("/api/agents")
    assert response.status_code == 200
    names = {agent["name"] for agent in response.json()["agents"]}
    assert names == {"sql", "rag", "research"}


def test_sql_question(client):
    response = client.post("/api/chat", json={"message": "What was total revenue in 2025?"})
    assert response.status_code == 200
    body = response.json()
    assert body["agents"] == ["sql"]
    assert body["data"]["sql"]["row_count"] == 1
    assert "$" in body["answer"]


def test_rag_question(client):
    response = client.post("/api/chat", json={"message": "What is the refund policy?"})
    assert response.status_code == 200
    body = response.json()
    assert body["agents"] == ["rag"]
    assert body["sources"]
    assert "30 days" in body["answer"].lower()


def test_research_question(client):
    response = client.post(
        "/api/chat",
        json={"message": "Summarize the latest agentic AI market trends and best practices."},
    )
    assert response.status_code == 200
    body = response.json()
    assert "research" in body["agents"]
    assert any(source["type"] == "web" for source in body["sources"])


def test_multi_agent_question(client):
    response = client.post(
        "/api/chat",
        json={"message": "How many cancelled orders do we have and what is the refund policy?"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "sql" in body["agents"]
    assert "rag" in body["agents"]
    assert len(body["tool_calls"]) >= 2


def test_validation(client):
    response = client.post("/api/chat", json={"message": ""})
    assert response.status_code == 422
