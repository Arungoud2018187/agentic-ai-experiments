const AGENT_LABELS = {
  sql: "SQL",
  rag: "Knowledge",
  research: "Research",
};

function confidenceLabel(value) {
  if (typeof value !== "number") return null;
  return `${Math.round(value * 100)}% confidence`;
}

function SourceList({ sources }) {
  if (!sources?.length) return null;

  return (
    <details className="response-details">
      <summary>
        {sources.length} source{sources.length === 1 ? "" : "s"}
        <span className="summary-chevron">⌄</span>
      </summary>
      <ul className="source-list">
        {sources.map((source, index) => (
          <li key={`${source.type}-${source.id || source.title}-${index}`}>
            <span className={`source-type type-${source.type}`}>{source.type === "knowledge_base" ? "KB" : source.type}</span>
            <div>
              {source.url ? (
                <a href={source.url} target="_blank" rel="noreferrer">
                  {source.title}
                </a>
              ) : (
                <strong>{source.title}</strong>
              )}
              {source.snippet && <p>{source.snippet}</p>}
            </div>
          </li>
        ))}
      </ul>
    </details>
  );
}

function SqlTable({ data }) {
  if (!data?.columns?.length || !data?.rows?.length) return null;

  return (
    <details className="response-details">
      <summary>
        Query result · {data.row_count} row{data.row_count === 1 ? "" : "s"}
        <span className="summary-chevron">⌄</span>
      </summary>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              {data.columns.map((column) => (
                <th key={column}>{column.replaceAll("_", " ")}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.rows.map((row, rowIndex) => (
              <tr key={rowIndex}>
                {data.columns.map((column) => (
                  <td key={column}>{row[column]}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <pre className="sql-block">{data.sql}</pre>
    </details>
  );
}

export default function Response({ message }) {
  const response = message.response;

  if (!response) {
    return (
      <article className={`response-card ${message.error ? "is-error" : ""}`}>
        <p className="answer-text">{message.content}</p>
      </article>
    );
  }

  const sqlData = response.data?.sql;

  return (
    <article className="response-card">
      <div className="response-header">
        <div className="agent-badges">
          {(response.agents || []).map((agent) => (
            <span key={agent} className={`agent-badge badge-${agent}`}>
              {AGENT_LABELS[agent] || agent}
            </span>
          ))}
        </div>
        <div className="response-meta">
          {confidenceLabel(response.confidence) && <span>{confidenceLabel(response.confidence)}</span>}
          {typeof response.latency_ms === "number" && <span>{Math.round(response.latency_ms)} ms</span>}
          {response.provider && <span>{response.provider === "offline" ? "offline rules" : response.provider}</span>}
        </div>
      </div>

      <div className="answer-text">{response.answer}</div>

      {response.routing?.reason && <p className="routing-note">{response.routing.reason}</p>}

      <SqlTable data={sqlData} />
      <SourceList sources={response.sources} />
    </article>
  );
}
