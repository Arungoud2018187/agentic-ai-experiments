const DEFAULT_AGENTS = [
  { name: "sql", description: "Operational data in SQLite", status: "ready" },
  { name: "rag", description: "Cited knowledge retrieval", status: "ready" },
  { name: "research", description: "Market and web synthesis", status: "ready" },
];

const AGENT_META = {
  sql: { label: "SQL analyst", icon: "▤", tone: "amber" },
  rag: { label: "Knowledge agent", icon: "◈", tone: "mint" },
  research: { label: "Research agent", icon: "◎", tone: "violet" },
};

export default function AgentStatus({ health, response, healthError }) {
  const agents = health?.agents?.length ? health.agents : DEFAULT_AGENTS;
  const active = new Set(response?.agents || []);
  const scores = response?.routing?.scores || {};
  const maxScore = Math.max(1, ...Object.values(scores));

  return (
    <section className="side-card">
      <div className="side-card-header">
        <div>
          <span className="side-eyebrow">Orchestration</span>
          <h2>Agent mesh</h2>
        </div>
        <span className={`mesh-status ${healthError ? "is-offline" : ""}`}>
          <i />
          {healthError ? "offline" : "ready"}
        </span>
      </div>

      <div className="agent-list">
        {agents.map((agent) => {
          const meta = AGENT_META[agent.name] || AGENT_META.rag;
          const isActive = active.has(agent.name);
          return (
            <div key={agent.name} className={`agent-row ${isActive ? "is-active" : ""}`}>
              <div className={`agent-icon tone-${meta.tone}`}>{meta.icon}</div>
              <div className="agent-copy">
                <div className="agent-name">
                  {meta.label}
                  {isActive && <span className="active-tag">active</span>}
                </div>
                <p>{agent.description}</p>
              </div>
              <span className={`agent-dot ${agent.status === "ready" ? "is-ready" : ""}`} />
            </div>
          );
        })}
      </div>

      {response && (
        <div className="routing-block">
          <div className="routing-title">
            <span>Routing score</span>
            <strong>{Math.round((response.confidence || 0) * 100)}%</strong>
          </div>
          {Object.entries(scores).map(([name, score]) => (
            <div className="score-row" key={name}>
              <span>{AGENT_META[name]?.label || name}</span>
              <div className="score-track">
                <div
                  className={`score-fill fill-${AGENT_META[name]?.tone || "mint"}`}
                  style={{ width: `${Math.max(3, (score / maxScore) * 100)}%` }}
                />
              </div>
              <em>{score}</em>
            </div>
          ))}
          {response.routing?.reason && <p className="routing-reason">{response.routing.reason}</p>}
        </div>
      )}

      <div className="connection-list">
        <div>
          <span>Database</span>
          <strong>{health?.database?.counts?.orders ?? "—"} orders</strong>
        </div>
        <div>
          <span>Knowledge</span>
          <strong>{health?.knowledge_base?.chunks ?? "—"} chunks</strong>
        </div>
        <div>
          <span>LLM mode</span>
          <strong>{health?.llm?.active_provider ?? "offline"}</strong>
        </div>
      </div>
    </section>
  );
}
