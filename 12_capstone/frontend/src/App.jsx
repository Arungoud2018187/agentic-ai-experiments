import { useCallback, useEffect, useState } from "react";

import Dashboard from "./pages/Dashboard";
import { getExamples, getHealth, sendMessage } from "./services/api";

const FALLBACK_EXAMPLES = [
  "What was total revenue in 2025?",
  "Which five customers generated the most revenue?",
  "What is the refund policy?",
  "Compare NovaDesk pricing with the market and summarize the latest agentic AI trends.",
  "How many open support tickets are there and what is our SLA?",
];

function makeId() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `msg-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export default function App() {
  const [messages, setMessages] = useState([]);
  const [examples, setExamples] = useState(FALLBACK_EXAMPLES);
  const [health, setHealth] = useState(null);
  const [healthError, setHealthError] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const refreshHealth = useCallback(async () => {
    try {
      const payload = await getHealth();
      setHealth(payload);
      setHealthError("");
    } catch (requestError) {
      setHealth(null);
      setHealthError(requestError.message);
    }
  }, []);

  useEffect(() => {
    refreshHealth();
    getExamples()
      .then((payload) => {
        if (payload?.examples?.length) setExamples(payload.examples);
      })
      .catch(() => {
        // The fallback suggestions keep the UI usable when the API is down.
      });
  }, [refreshHealth]);

  const handleSend = useCallback(
    async (rawText) => {
      const question = rawText.trim();
      if (!question || loading) return;

      setError("");
      setMessages((current) => [
        ...current,
        { id: makeId(), role: "user", content: question },
      ]);
      setLoading(true);

      try {
        const response = await sendMessage(question);
        setMessages((current) => [
          ...current,
          { id: response.id || makeId(), role: "assistant", content: response.answer, response },
        ]);
        setHealth((current) => (current ? { ...current, status: "ok" } : current));
      } catch (requestError) {
        setError(requestError.message);
        setMessages((current) => [
          ...current,
          {
            id: makeId(),
            role: "assistant",
            content: `I could not reach the agent service. ${requestError.message}`,
            error: true,
          },
        ]);
      } finally {
        setLoading(false);
      }
    },
    [loading]
  );

  const handleReset = () => {
    setMessages([]);
    setError("");
  };

  return (
    <Dashboard
      messages={messages}
      examples={examples}
      loading={loading}
      error={error}
      health={health}
      healthError={healthError}
      onSend={handleSend}
      onReset={handleReset}
      onRefreshHealth={refreshHealth}
    />
  );
}
