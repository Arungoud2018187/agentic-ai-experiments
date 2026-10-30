const STATUS_LABELS = {
  success: "ok",
  empty: "empty",
  error: "error",
};

export default function ToolPanel({ response }) {
  const toolCalls = response?.tool_calls || [];

  return (
    <section className="side-card tool-card-panel">
      <div className="side-card-header">
        <div>
          <span className="side-eyebrow">Observability</span>
          <h2>Execution trace</h2>
        </div>
        <span className="trace-count">{toolCalls.length}</span>
      </div>

      {toolCalls.length === 0 ? (
        <div className="trace-empty">
          <div className="trace-empty-icon">⌁</div>
          <p>Tool calls appear here after your first question.</p>
          <span>SQL queries, retrieval lookups and research searches are all logged.</span>
        </div>
      ) : (
        <div className="trace-list">
          {toolCalls.map((call, index) => {
            const status = STATUS_LABELS[call.status] || call.status || "ok";
            return (
              <details className="trace-item" key={`${call.tool}-${index}`}>
                <summary>
                  <span className={`trace-status status-${call.status || "success"}`} />
                  <div className="trace-summary">
                    <strong>{call.tool}</strong>
                    <span>
                      {call.agent || "agent"} · {status}
                      {typeof call.latency_ms === "number" ? ` · ${Math.round(call.latency_ms)} ms` : ""}
                    </span>
                  </div>
                  <span className="summary-chevron">⌄</span>
                </summary>
                <div className="trace-detail">
                  <label>Input</label>
                  <pre>{call.input}</pre>
                  <label>Output</label>
                  <pre>{call.output}</pre>
                </div>
              </details>
            );
          })}
        </div>
      )}

      {response?.llm && (
        <div className="synthesis-note">
          <span className="synthesis-dot" />
          <div>
            <strong>Synthesis layer</strong>
            <p>
              {response.llm.fallback
                ? "Offline deterministic composer"
                : `${response.llm.provider} · ${response.llm.model}`}
            </p>
          </div>
        </div>
      )}
    </section>
  );
}
