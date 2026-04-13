import { useEffect, useMemo, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import Navbar from "../components/Navbar";
import {
  explainLatestCase,
  getChatSessionMessages,
  getChatSessions,
  queryChatbot,
  deleteChatSession,
  deleteRecentChats,
} from "../services/api";
import "./chatbot.css";

function formatTime(value) {
  if (!value) return "";
  try {
    return new Date(value).toLocaleString();
  } catch {
    return "";
  }
}

function normalizeSources(value) {
  if (!Array.isArray(value)) return [];

  const seen = new Set();
  const cleaned = [];

  for (const item of value) {
    if (!item || typeof item !== "object") continue;

    const title = (item.title || "").trim();
    const source = (item.source || "").trim();
    const url = (item.url || "").trim();
    const chunkId = (item.chunk_id || "").trim();

    if (!title && !url) continue;

    const key = `${title}__${source}__${chunkId}__${url}`;
    if (seen.has(key)) continue;
    seen.add(key);

    cleaned.push({
      title: title || "Medical reference",
      source,
      url,
      chunk_id: chunkId,
    });
  }

  return cleaned;
}

function SourceLine({ sources }) {
  if (!Array.isArray(sources) || sources.length === 0) return null;

  return (
    <div className="chatbot-references">
      <span className="chatbot-references-label">References:</span>
      <span className="chatbot-references-items">
        {sources.map((source, index) => (
          <span key={`${source.title || "source"}-${index}`}>
            {index > 0 ? " · " : ""}
            {source.url ? (
              <a href={source.url} target="_blank" rel="noreferrer">
                {source.title || "Medical reference"}
              </a>
            ) : (
              <span>{source.title || "Medical reference"}</span>
            )}
          </span>
        ))}
      </span>
    </div>
  );
}

function MessageBubble({ message }) {
  const isUser = message.role === "user";

  return (
    <div className={`chatbot-message-row ${isUser ? "user" : "assistant"}`}>
      <div className={`chatbot-message-bubble ${isUser ? "user" : "assistant"}`}>
        <div className="chatbot-message-text">
          {isUser ? (
            message.content
          ) : (
            <ReactMarkdown>{message.content}</ReactMarkdown>
          )}
        </div>

        {!isUser && message.used_case_summary ? (
          <div className="chatbot-case-summary">
            <div className="chatbot-case-summary-title">
              Case details used for this answer
            </div>
            <div className="chatbot-case-summary-text">
              {message.used_case_summary}
            </div>
          </div>
        ) : null}

        {!isUser ? <SourceLine sources={message.sources} /> : null}

        <div className="chatbot-message-time">{formatTime(message.created_at)}</div>
      </div>
    </div>
  );
}

function Chatbot() {
  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [messages, setMessages] = useState([
    {
      id: "welcome",
      role: "assistant",
      content:
        "Ask a breast-cancer-related educational question, or use “Explain Latest Case” for a case-aware explanation.",
      sources: [],
      created_at: new Date().toISOString(),
    },
  ]);
  const [input, setInput] = useState("");
  const [loadingSessions, setLoadingSessions] = useState(true);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [sending, setSending] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState("");

  const messagesEndRef = useRef(null);

  useEffect(() => {
    loadSessions();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  async function loadSessions() {
    try {
      setLoadingSessions(true);
      setError("");

      const data = await getChatSessions();
      setSessions(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err.message || "Failed to load chat history.");
    } finally {
      setLoadingSessions(false);
    }
  }

  async function openSession(sessionId) {
    try {
      setLoadingMessages(true);
      setError("");
      setActiveSessionId(sessionId);

      const data = await getChatSessionMessages(sessionId);

      const loadedMessages = Array.isArray(data?.messages) ? data.messages : [];
      const normalizedMessages = loadedMessages.map((message) => ({
        ...message,
        sources: normalizeSources(message.sources || message.sources_json),
      }));

      setMessages(
        normalizedMessages.length > 0
          ? normalizedMessages
          : [
              {
                id: "empty",
                role: "assistant",
                content: "This session has no messages yet.",
                sources: [],
                created_at: new Date().toISOString(),
              },
            ]
      );
    } catch (err) {
      setError(err.message || "Failed to load session messages.");
    } finally {
      setLoadingMessages(false);
    }
  }

  function startNewChat() {
    setActiveSessionId(null);
    setMessages([
      {
        id: "welcome-new",
        role: "assistant",
        content:
          "New chat started. Ask about IDC, DCIS, biopsy, grading, staging, HER2, pathology, or explain your latest saved case.",
        sources: [],
        created_at: new Date().toISOString(),
      },
    ]);
    setError("");
    setInput("");
  }

  async function handleSend() {
    const trimmed = input.trim();
    if (!trimmed || sending) return;

    const optimisticUserMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: trimmed,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, optimisticUserMessage]);
    setInput("");
    setSending(true);
    setError("");

    try {
      const result = await queryChatbot({
        message: trimmed,
        session_id: activeSessionId,
        use_latest_case: false,
      });

      const assistantMessage = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: result.answer,
        sources: normalizeSources(result.sources),
        used_case_summary: result.used_case_summary || null,
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMessage]);

      if (result.session_id) {
        setActiveSessionId(result.session_id);
      }

      await loadSessions();
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: `assistant-error-${Date.now()}`,
          role: "assistant",
          content: err.message || "Failed to get chatbot response.",
          sources: [],
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setSending(false);
    }
  }

  async function handleExplainLatestCase() {
    if (sending) return;

    setSending(true);
    setError("");

    const optimisticUserMessage = {
      id: `user-case-${Date.now()}`,
      role: "user",
      content: "Explain my latest case.",
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, optimisticUserMessage]);

    try {
      const result = await explainLatestCase(activeSessionId);

      const assistantMessage = {
        id: `assistant-case-${Date.now()}`,
        role: "assistant",
        content: result.answer,
        sources: normalizeSources(result.sources),
        used_case_summary: result.used_case_summary || null,
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMessage]);

      if (result.session_id) {
        setActiveSessionId(result.session_id);
      }

      await loadSessions();
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: `assistant-case-error-${Date.now()}`,
          role: "assistant",
          content: err.message || "Failed to explain latest case.",
          sources: [],
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setSending(false);
    }
  }

  async function handleDeleteSession(sessionId, event) {
    event.stopPropagation();

    const confirmed = window.confirm("Delete this chat session?");
    if (!confirmed) return;

    try {
      setDeleting(true);
      setError("");

      await deleteChatSession(sessionId);

      const wasActive = activeSessionId === sessionId;

      await loadSessions();

      if (wasActive) {
        setActiveSessionId(null);
        setMessages([
          {
            id: "welcome-after-delete",
            role: "assistant",
            content:
              "Chat session deleted. You can start a new chat or open another saved session.",
            sources: [],
            created_at: new Date().toISOString(),
          },
        ]);
      }
    } catch (err) {
      setError(err.message || "Failed to delete chat session.");
    } finally {
      setDeleting(false);
    }
  }

  async function handleDeleteRecentChats() {
    const confirmed = window.confirm("Delete the 5 most recent chat sessions?");
    if (!confirmed) return;

    try {
      setDeleting(true);
      setError("");

      await deleteRecentChats(5);
      setActiveSessionId(null);
      setMessages([
        {
          id: "welcome-after-recent-delete",
          role: "assistant",
          content:
            "Recent chats deleted. You can start a new chat whenever you're ready.",
          sources: [],
          created_at: new Date().toISOString(),
        },
      ]);

      await loadSessions();
    } catch (err) {
      setError(err.message || "Failed to delete recent chats.");
    } finally {
      setDeleting(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  const visibleSessions = useMemo(() => {
    return Array.isArray(sessions) ? sessions : [];
  }, [sessions]);

  return (
    <div className="chatbot-page">
      <Navbar />

      <div className="chatbot-layout">
        <aside className="chatbot-sidebar">
          <div className="chatbot-sidebar-header">
            <div>
              <div className="chatbot-kicker">MedScan AI</div>
              <h2>Chat Sessions</h2>
            </div>

            <div className="chatbot-sidebar-actions">
              <button className="chatbot-new-btn" onClick={startNewChat}>
                + New Chat
              </button>
              <button
                className="chatbot-delete-recent-btn"
                onClick={handleDeleteRecentChats}
                disabled={deleting || loadingSessions || visibleSessions.length === 0}
              >
                Delete Recent
              </button>
            </div>
          </div>

          {loadingSessions ? (
            <div className="chatbot-sidebar-empty">Loading sessions...</div>
          ) : visibleSessions.length === 0 ? (
            <div className="chatbot-sidebar-empty">No chat sessions yet.</div>
          ) : (
            <div className="chatbot-session-list">
              {visibleSessions.map((session) => (
                <div
                  key={session.id}
                  className={`chatbot-session-item ${
                    activeSessionId === session.id ? "active" : ""
                  }`}
                >
                  <button
                    className="chatbot-session-open"
                    onClick={() => openSession(session.id)}
                  >
                    <div className="chatbot-session-title">{session.title}</div>
                    <div className="chatbot-session-time">
                      {formatTime(session.updated_at)}
                    </div>
                  </button>

                  <button
                    className="chatbot-session-delete"
                    onClick={(event) => handleDeleteSession(session.id, event)}
                    disabled={deleting}
                    title="Delete this chat"
                  >
                    Delete
                  </button>
                </div>
              ))}
            </div>
          )}
        </aside>

        <main className="chatbot-main">
          <div className="chatbot-main-header">
            <div>
              <div className="chatbot-kicker">Educational Assistant</div>
              <h1>Breast Cancer Chatbot</h1>
              <p>
                Grounded educational chatbot for breast-cancer topics and saved case explanations.
              </p>
            </div>

            <button
              className="chatbot-case-btn"
              onClick={handleExplainLatestCase}
              disabled={sending}
            >
              Explain Latest Case
            </button>
          </div>

          {error ? <div className="chatbot-error">{error}</div> : null}

          <div className="chatbot-messages">
            {loadingMessages ? (
              <div className="chatbot-loading">Loading conversation...</div>
            ) : (
              messages.map((message) => (
                <MessageBubble key={message.id} message={message} />
              ))
            )}

            {sending ? (
              <div className="chatbot-message-row assistant">
                <div className="chatbot-message-bubble assistant">
                  <div className="chatbot-typing">Thinking...</div>
                </div>
              </div>
            ) : null}

            <div ref={messagesEndRef} />
          </div>

          <div className="chatbot-input-wrap">
            <textarea
              className="chatbot-input"
              rows={3}
              placeholder="Ask about IDC, DCIS, biopsy, grading, staging, HER2, pathology, metastasis, or your saved case..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={sending}
            />

            <div className="chatbot-input-actions">
              <div className="chatbot-input-note">
                Educational only — not for clinical diagnosis.
              </div>

              <button
                className="chatbot-send-btn"
                onClick={handleSend}
                disabled={sending || !input.trim()}
              >
                Send
              </button>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

export default Chatbot;