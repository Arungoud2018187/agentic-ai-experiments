const API_BASE = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");

async function request(path, options = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 30000);

  try {
    const response = await fetch(`${API_BASE}${path}`, {
      ...options,
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
    });

    if (!response.ok) {
      let detail = `Request failed with status ${response.status}`;
      try {
        const body = await response.json();
        if (body.detail) detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
      } catch {
        // Keep the status-based message when the body is not JSON.
      }
      throw new Error(detail);
    }

    return await response.json();
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error("The request timed out. Is the backend running?");
    }
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}

export function getHealth() {
  return request("/api/health");
}

export function getExamples() {
  return request("/api/examples");
}

export function sendMessage(message) {
  return request("/api/chat", {
    method: "POST",
    body: JSON.stringify({ message, include_trace: true }),
  });
}
