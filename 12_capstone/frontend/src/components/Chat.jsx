import { useEffect, useRef, useState } from "react";

import Response from "./Response";

export default function Chat({ messages, examples, loading, error, healthError, onSend }) {
  const [input, setInput] = useState("");
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, loading]);

  const submit = (event) => {
    event?.preventDefault();
    if (!input.trim() || loading) return;
    onSend(input);
    setInput("");
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      submit();
    }
  };

  return (
    <div className="chat-panel">
      {healthError && (
        <div className="health-banner">
          <strong>Backend not reachable.</strong> Start it with{" "}
          <code>uvicorn app.main:app --reload</code> from the backend folder.
          <span>{healthError}</span>
        </div>
      )}

      <div className="message-scroll">
        {messages.length === 0 ? (
          <div className="empty-state">
            <span className="eyebrow">One prompt · three specialists</span>
            <h1>
              Ask across data, documents,
              <br />
              and the open web.
            </h1>
            <p className="empty-copy">
              The supervisor routes every question to a SQL analyst, a knowledge retrieval agent, or a
              research analyst — then combines the evidence with a trace you can audit.
            </p>

            <div className="suggestion-grid">
              {examples.slice(0, 6).map((example) => (
                <button
                  key={example}
                  type="button"
                  className="suggestion-card"
                  onClick={() => onSend(example)}
                  disabled={loading}
                >
                  <span className="suggestion-arrow">↗</span>
                  {example}
                </button>
              ))}
            </div>

            <div className="empty-metrics">
              <div>
                <span>SQL rows</span>
                <strong>120 orders</strong>
              </div>
              <div>
                <span>Knowledge base</span>
                <strong>10 documents</strong>
              </div>
              <div>
                <span>Research index</span>
                <strong>8 sources</strong>
              </div>
            </div>
          </div>
        ) : (
          <div className="message-list">
            {messages.map((message) =>
              message.role === "user" ? (
                <div className="message-row is-user" key={message.id}>
                  <div className="user-bubble">{message.content}</div>
                  <div className="message-avatar user-avatar">You</div>
                </div>
              ) : (
                <div className="message-row is-assistant" key={message.id}>
                  <div className="message-avatar assistant-avatar">N</div>
                  <div className="assistant-content">
                    <Response message={message} />
                  </div>
                </div>
              )
            )}

            {loading && (
              <div className="message-row is-assistant">
                <div className="message-avatar assistant-avatar is-thinking">N</div>
                <div className="thinking-card">
                  <span className="thinking-label">Supervisor is planning</span>
                  <span className="thinking-dots">
                    <i />
                    <i />
                    <i />
                  </span>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      {error && messages.length > 0 && (
        <div className="inline-error">
          <span>Request failed:</span> {error}
        </div>
      )}

      <form className="composer" onSubmit={submit}>
        <div className="composer-input-wrap">
          <textarea
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about revenue, policies, integrations, or market trends…"
            rows={1}
            maxLength={2000}
            disabled={loading}
            aria-label="Ask the assistant"
          />
          <button type="submit" className="send-button" disabled={!input.trim() || loading}>
            <span>Send</span>
            <span className="send-icon">↑</span>
          </button>
        </div>
        <div className="composer-note">
          <span>Enter to send · Shift + Enter for a new line</span>
          <span>Grounded answers · Audit-ready trace</span>
        </div>
      </form>
    </div>
  );
}
