import AgentStatus from "../components/AgentStatus";
import Chat from "../components/Chat";
import ToolPanel from "../components/ToolPanel";

export default function Dashboard({
  messages,
  examples,
  loading,
  error,
  health,
  healthError,
  onSend,
  onReset,
  onRefreshHealth,
}) {
  const latestAssistant = [...messages].reverse().find((message) => message.role === "assistant" && message.response);
  const response = latestAssistant?.response;
  const online = health?.status === "ok";

  return (
    <div className="app-shell">
      <div className="ambient ambient-one" />
      <div className="ambient ambient-two" />

      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">N</div>
          <div>
            <div className="brand-name">NovaDesk</div>
            <div className="brand-subtitle">Agentic operations console</div>
          </div>
        </div>

        <div className="topbar-actions">
          <button
            type="button"
            className={`status-pill ${online ? "is-online" : "is-offline"}`}
            onClick={onRefreshHealth}
            title="Refresh backend health"
          >
            <span className="status-dot" />
            {online ? "Agents online" : "Backend offline"}
          </button>
          <button type="button" className="ghost-button" onClick={onReset}>
            New chat
          </button>
        </div>
      </header>

      <main className="workspace">
        <section className="chat-column">
          <Chat
            messages={messages}
            examples={examples}
            loading={loading}
            error={error}
            healthError={healthError}
            onSend={onSend}
          />
        </section>

        <aside className="sidebar">
          <AgentStatus health={health} response={response} healthError={healthError} />
          <ToolPanel response={response} />
        </aside>
      </main>
    </div>
  );
}
