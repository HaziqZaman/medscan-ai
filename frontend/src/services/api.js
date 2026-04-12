const API_BASE = "http://127.0.0.1:8000";

function getToken() {
  return localStorage.getItem("token");
}

function buildHeaders(extra = {}) {
  const token = getToken();

  return {
    ...extra,
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

async function parseResponse(response) {
  let data = null;

  try {
    data = await response.json();
  } catch {
    data = null;
  }

  if (!response.ok) {
    throw new Error(data?.detail || "Request failed");
  }

  return data;
}

export async function runAnalysis(imageFile) {
  const formData = new FormData();
  formData.append("file", imageFile);

  const response = await fetch(`${API_BASE}/analysis/predict`, {
    method: "POST",
    headers: buildHeaders(),
    body: formData,
  });

  return parseResponse(response);
}

export async function queryChatbot(payload) {
  const response = await fetch(`${API_BASE}/chatbot/query`, {
    method: "POST",
    headers: buildHeaders({
      "Content-Type": "application/json",
    }),
    body: JSON.stringify(payload),
  });

  return parseResponse(response);
}

export async function explainLatestCase(sessionId = null) {
  const response = await fetch(`${API_BASE}/chatbot/explain-latest-case`, {
    method: "POST",
    headers: buildHeaders({
      "Content-Type": "application/json",
    }),
    body: JSON.stringify({
      session_id: sessionId,
      message: "Explain my latest case in simple educational terms.",
    }),
  });

  return parseResponse(response);
}

export async function getChatSessions() {
  const response = await fetch(`${API_BASE}/chatbot/history`, {
    method: "GET",
    headers: buildHeaders(),
  });

  return parseResponse(response);
}

export async function getChatSessionMessages(sessionId) {
  const response = await fetch(`${API_BASE}/chatbot/history/${sessionId}`, {
    method: "GET",
    headers: buildHeaders(),
  });

  return parseResponse(response);
}

export async function getCases() {
  const response = await fetch(`${API_BASE}/cases`, {
    method: "GET",
    headers: buildHeaders(),
  });

  return parseResponse(response);
}

export { API_BASE };