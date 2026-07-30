"use client";

// components/BrandAssistant.tsx
// AI Growth Assistant chat panel.
// Calls POST /api/backend/api/chat and maintains conversation history.

import { useState, useRef, useEffect, FormEvent } from "react";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface BrandAssistantProps {
  /** Pre-filled business context from the main form */
  businessName: string;
  businessType: string;
}

// ── Spinner ──────────────────────────────────────────────────────────────────

function Spinner() {
  return (
    <span className="inline-flex gap-1 items-center">
      {[0, 150, 300].map((delay) => (
        <span
          key={delay}
          className="w-1.5 h-1.5 rounded-full animate-bounce-slow"
          style={{ background: "var(--accent)", animationDelay: `${delay}ms`, display: "inline-block" }}
        />
      ))}
    </span>
  );
}

// ── Avatars ───────────────────────────────────────────────────────────────────

function AiAvatar() {
  return (
    <div
      className="w-7 h-7 rounded-lg shrink-0 flex items-center justify-center"
      style={{ background: "linear-gradient(135deg, #7c6dfa, #5b4de0)" }}
    >
      <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
        <circle cx="7" cy="7" r="2.5" fill="rgba(255,255,255,.9)"/>
        <line x1="7" y1="1" x2="7" y2="4.2"  stroke="rgba(255,255,255,.7)" strokeWidth="1.2" strokeLinecap="round"/>
        <line x1="7" y1="9.8" x2="7" y2="13" stroke="rgba(255,255,255,.7)" strokeWidth="1.2" strokeLinecap="round"/>
        <line x1="1" y1="7" x2="4.2" y2="7"  stroke="rgba(255,255,255,.7)" strokeWidth="1.2" strokeLinecap="round"/>
        <line x1="9.8" y1="7" x2="13" y2="7" stroke="rgba(255,255,255,.7)" strokeWidth="1.2" strokeLinecap="round"/>
      </svg>
    </div>
  );
}

function UserAvatar() {
  return (
    <div
      className="w-7 h-7 rounded-lg shrink-0 flex items-center justify-center"
      style={{ background: "var(--bg-card)", border: "1px solid var(--bg-border)" }}
    >
      <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
        <circle cx="7" cy="5" r="2.5" stroke="var(--text-secondary)" strokeWidth="1.2" fill="none"/>
        <path d="M2 13 C2 10 4 8.5 7 8.5 C10 8.5 12 10 12 13" stroke="var(--text-secondary)" strokeWidth="1.2" strokeLinecap="round" fill="none"/>
      </svg>
    </div>
  );
}

// ── Message bubble ────────────────────────────────────────────────────────────

function Bubble({ message }: { message: Message }) {
  const isUser = message.role === "user";
  return (
    <div className={`flex gap-2.5 ${isUser ? "flex-row-reverse" : "flex-row"} mb-3`}>
      <div className="shrink-0 mt-0.5">
        {isUser ? <UserAvatar /> : <AiAvatar />}
      </div>
      <div
        className={`max-w-[80%] px-3.5 py-2.5 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
          isUser ? "rounded-tr-sm" : "rounded-tl-sm"
        }`}
        style={
          isUser
            ? {
                background: "linear-gradient(135deg, #7c6dfa, #5b4de0)",
                color: "#fff",
                boxShadow: "0 4px 16px rgba(124,109,250,0.25)",
              }
            : {
                background: "var(--bg-elevated)",
                border: "1px solid var(--bg-border)",
                color: "var(--text-primary)",
              }
        }
      >
        {message.content}
      </div>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export default function BrandAssistant({
  businessName,
  businessType,
}: BrandAssistantProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: `Hello! I'm your Brand Growth Assistant. I'm here to help you grow ${businessName || "your business"} with smart, ethical marketing strategies. What would you like advice on today?`,
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef  = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function sendMessage(e: FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading) return;

    const userMessage: Message = { role: "user", content: text };
    const updatedHistory = [...messages, userMessage];

    setMessages(updatedHistory);
    setInput("");
    setLoading(true);
    setError(null);

    try {
      const res = await fetch("/api/backend/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_message:  text,
          business_name: businessName,
          business_type: businessType,
          chat_history:  messages.map(({ role, content }) => ({ role, content })),
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(
          errData?.detail || `Server error (${res.status}). Please try again.`
        );
      }

      const data = await res.json();
      // /api/chat returns { text, artifact_html } — not { reply }
      const reply = (data?.text || "").trim();

      if (!reply) throw new Error("The assistant returned an empty response.");

      setMessages([...updatedHistory, { role: "assistant", content: reply }]);
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : "An unexpected error occurred.";
      setError(msg);
      // Remove the user message that failed so the user can retry
      setMessages(messages);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(e as unknown as FormEvent);
    }
  }

  return (
    <div
      className="flex flex-col h-full overflow-hidden"
      style={{ background: "var(--bg-surface)", border: "1px solid var(--bg-border)", borderRadius: "inherit" }}
    >
      {/* ── Header ─────────────────────────────────────────────── */}
      <div
        className="px-4 py-3 shrink-0 flex items-center gap-3"
        style={{ borderBottom: "1px solid var(--bg-border)", background: "var(--bg-elevated)" }}
      >
        <div
          className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0"
          style={{ background: "linear-gradient(135deg, #7c6dfa, #5b4de0)" }}
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="rgba(255,255,255,0.9)" className="w-4 h-4">
            <path d="M15.98 1.804a1 1 0 0 0-1.96 0l-.24 1.192a1 1 0 0 1-.784.784l-1.192.24a1 1 0 0 0 0 1.96l1.192.24a1 1 0 0 1 .784.784l.24 1.192a1 1 0 0 0 1.96 0l.24-1.192a1 1 0 0 1 .784-.784l1.192-.24a1 1 0 0 0 0-1.96l-1.192-.24a1 1 0 0 1-.784-.784l-.24-1.192ZM6.949 5.684a1 1 0 0 0-1.898 0l-.683 2.051a1 1 0 0 1-.633.633l-2.051.683a1 1 0 0 0 0 1.898l2.051.683a1 1 0 0 1 .633.633l.683 2.051a1 1 0 0 0 1.898 0l.683-2.051a1 1 0 0 1 .633-.633l2.051-.683a1 1 0 0 0 0-1.898l-2.051-.683a1 1 0 0 1-.633-.633L6.949 5.684Z" />
          </svg>
        </div>
        <div className="flex flex-col leading-none gap-0.5">
          <p className="font-display text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
            Brand Growth Assistant
          </p>
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>
            AI-powered strategy &amp; content advisor
          </p>
        </div>
        <div className="ml-auto flex items-center gap-1.5">
          <span className="dot-live" />
          <span className="text-xs" style={{ color: "var(--text-muted)" }}>Online</span>
        </div>
      </div>

      {/* ── Messages ───────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto px-4 py-3">
        {messages.map((msg, i) => (
          <Bubble key={i} message={msg} />
        ))}
        {loading && (
          <div className="flex gap-2.5 mb-3">
            <AiAvatar />
            <div
              className="px-3.5 py-2.5 rounded-2xl rounded-tl-sm flex items-center"
              style={{ background: "var(--bg-elevated)", border: "1px solid var(--bg-border)" }}
            >
              <Spinner />
            </div>
          </div>
        )}
        {error && (
          <div
            className="text-xs rounded-lg px-3 py-2 mb-2"
            style={{
              color: "var(--rose)",
              background: "var(--rose-muted)",
              border: "1px solid rgba(251,113,133,0.2)",
            }}
          >
            {error}
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* ── Input ──────────────────────────────────────────────── */}
      <form
        onSubmit={sendMessage}
        className="shrink-0 px-4 py-3"
        style={{ borderTop: "1px solid var(--bg-border)", background: "var(--bg-surface)" }}
      >
        <div
          className="flex items-end gap-2 rounded-2xl p-2"
          style={{
            background: "var(--bg-elevated)",
            border: `1px solid ${loading ? "var(--accent)" : "var(--bg-border)"}`,
            boxShadow: loading ? "0 0 0 3px var(--accent-glow)" : "none",
          }}
        >
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about marketing, content strategy, growth ideas…"
            rows={2}
            disabled={loading}
            className="flex-1 resize-none bg-transparent text-sm leading-relaxed py-1 px-2 border-0 outline-none disabled:opacity-50"
            style={{ color: "var(--text-primary)", caretColor: "var(--accent)" }}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="shrink-0 w-8 h-8 rounded-xl flex items-center justify-center transition-all disabled:opacity-40 disabled:cursor-not-allowed"
            style={{
              background: "linear-gradient(135deg, #7c6dfa, #5b4de0)",
              color: "#fff",
              cursor: loading || !input.trim() ? "not-allowed" : "pointer",
              boxShadow: "0 0 12px rgba(124,109,250,0.35)",
            }}
            title="Send message (Enter)"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4 rotate-90">
              <path d="M3.105 2.288a.75.75 0 0 0-.826.95l1.454 4.425H7.5a.75.75 0 0 1 0 1.5H3.733l-1.454 4.425a.75.75 0 0 0 .826.95 28.896 28.896 0 0 0 15.293-7.154.75.75 0 0 0 0-1.115A28.897 28.897 0 0 0 3.105 2.288Z" />
            </svg>
          </button>
        </div>
        <p className="mt-1.5 text-[10px] text-center" style={{ color: "var(--text-muted)" }}>
          Enter to send · Shift+Enter for new line
        </p>
      </form>
    </div>
  );
}
