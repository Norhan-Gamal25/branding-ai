"use client";

import { useState, useRef, useEffect } from "react";
import ArtifactRenderer from "./ArtifactRenderer";

interface Message {
  role: "user" | "assistant";
  content: string;
  artifactHtml?: string;
}

interface StrategyChatProps {
  businessContext: string;
  onArtifactGenerated?: (html: string) => void;
}

function parseArtifact(text: string): { text: string; artifact: string | null } {
  const match = text.match(/```html\s*([\s\S]*?)```/i);
  if (match) {
    const artifact = match[1].trim();
    const clean = (text.slice(0, match.index) + text.slice(match.index! + match[0].length)).trim();
    return { text: clean, artifact };
  }
  return { text, artifact: null };
}

/**
 * Markdown → HTML renderer for chat bubbles.
 * Handles: headings, bold, italic, inline code, unordered lists,
 * numbered lists, blockquotes, horizontal rules, and paragraphs.
 */
function renderMarkdown(text: string): string {
  const lines = text.split("\n");
  const output: string[] = [];
  let inUl = false;
  let inOl = false;

  const closeList = () => {
    if (inUl) { output.push("</ul>"); inUl = false; }
    if (inOl) { output.push("</ol>"); inOl = false; }
  };

  const inline = (s: string) =>
    s
      .replace(/`([^`]+)`/g, "<code>$1</code>")
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/\*(.+?)\*/g, "<em>$1</em>")
      .replace(/_(.+?)_/g, "<em>$1</em>");

  for (const raw of lines) {
    const line = raw.trimEnd();

    if (/^### (.+)$/.test(line)) {
      closeList();
      output.push(`<h3>${inline(line.slice(4))}</h3>`);
      continue;
    }
    if (/^## (.+)$/.test(line)) {
      closeList();
      output.push(`<h2>${inline(line.slice(3))}</h2>`);
      continue;
    }
    if (/^# (.+)$/.test(line)) {
      closeList();
      output.push(`<h1>${inline(line.slice(2))}</h1>`);
      continue;
    }
    if (/^---+$/.test(line)) {
      closeList();
      output.push("<hr/>");
      continue;
    }
    if (/^> (.+)$/.test(line)) {
      closeList();
      output.push(`<blockquote>${inline(line.slice(2))}</blockquote>`);
      continue;
    }
    const ulMatch = line.match(/^[-*•] (.+)$/);
    if (ulMatch) {
      if (inOl) { output.push("</ol>"); inOl = false; }
      if (!inUl) { output.push("<ul>"); inUl = true; }
      output.push(`<li>${inline(ulMatch[1])}</li>`);
      continue;
    }
    const olMatch = line.match(/^\d+\. (.+)$/);
    if (olMatch) {
      if (inUl) { output.push("</ul>"); inUl = false; }
      if (!inOl) { output.push("<ol>"); inOl = true; }
      output.push(`<li>${inline(olMatch[1])}</li>`);
      continue;
    }
    if (line.trim() === "") {
      closeList();
      output.push("<br/>");
      continue;
    }
    closeList();
    output.push(`<p>${inline(line)}</p>`);
  }

  closeList();
  return output.join("\n");
}

/* ── Quick prompt definitions ─────────────────────────────────────────────── */
const QUICK_PROMPTS: { label: string; icon: string; prompt: string }[] = [
  {
    label: "Logo concept",
    icon: "◈",
    prompt:
      "Design a logo concept for my brand as a self-contained HTML page using Tailwind CSS and Phosphor Icons. Show the brand name in a bold display font inside a styled container with relevant Phosphor Icons as decoration, displayed on both a dark and a light background. No SVG paths.",
  },
  {
    label: "Brand tagline",
    icon: "✦",
    prompt: "Write 5 compelling brand taglines with a brief explanation for each",
  },
  {
    label: "Colour palette",
    icon: "◉",
    prompt:
      "Create a complete brand colour palette as an HTML visual — show 5–6 colour swatches with their hex codes, names, and usage labels (Primary, Secondary, Accent, Background, Text). Use Tailwind CSS and a clean layout.",
  },
  {
    label: "Social post",
    icon: "◈",
    prompt:
      "Create a social media content pack for my brand: 3 post copy variants (Hero/Brand Statement, Value/Feature, Community/Story). For each post give me: a punchy headline, 2–4 sentences of body copy, 5 relevant hashtags, and a detailed photo description I can search on Unsplash or Pexels. End with 2–3 platform-specific posting tips.",
  },
];

/* ── Abstract AI avatar SVG ───────────────────────────────────────────────── */
function AiAvatar() {
  return (
    <div
      className="w-7 h-7 rounded-lg shrink-0 flex items-center justify-center"
      style={{ background: "linear-gradient(135deg, #7c6dfa, #5b4de0)" }}
    >
      {/* Abstract node/spark mark */}
      <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
        <circle cx="7" cy="7" r="2.5" fill="rgba(255,255,255,.9)"/>
        <line x1="7" y1="1" x2="7" y2="4.2"   stroke="rgba(255,255,255,.7)" strokeWidth="1.2" strokeLinecap="round"/>
        <line x1="7" y1="9.8" x2="7" y2="13"  stroke="rgba(255,255,255,.7)" strokeWidth="1.2" strokeLinecap="round"/>
        <line x1="1" y1="7" x2="4.2" y2="7"   stroke="rgba(255,255,255,.7)" strokeWidth="1.2" strokeLinecap="round"/>
        <line x1="9.8" y1="7" x2="13" y2="7"  stroke="rgba(255,255,255,.7)" strokeWidth="1.2" strokeLinecap="round"/>
      </svg>
    </div>
  );
}

function UserAvatar() {
  return (
    <div
      className="w-7 h-7 rounded-lg shrink-0 flex items-center justify-center"
      style={{
        background: "var(--bg-card)",
        border: "1px solid var(--bg-border)",
      }}
    >
      {/* Abstract user glyph */}
      <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
        <circle cx="7" cy="5" r="2.5" stroke="var(--text-secondary)" strokeWidth="1.2" fill="none"/>
        <path d="M2 13 C2 10 4 8.5 7 8.5 C10 8.5 12 10 12 13" stroke="var(--text-secondary)" strokeWidth="1.2" strokeLinecap="round" fill="none"/>
      </svg>
    </div>
  );
}

export default function StrategyChat({
  businessContext,
  onArtifactGenerated,
}: StrategyChatProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Hello! I'm your **Ethical Strategy Director**.\n\nAsk me anything — business strategy, marketing campaigns, visual assets, logo design, or brand identity.\n\nHow can I help you build something extraordinary today?",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [expandedArtifact, setExpandedArtifact] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // Auto-grow textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [input]);

  const sendMessage = async () => {
    const trimmed = input.trim();
    if (!trimmed || loading) return;

    const userMsg: Message = { role: "user", content: trimmed };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch("/api/backend/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_message: trimmed,
          business_context: businessContext,
          chat_history: messages.map((m) => ({ role: m.role, content: m.content })),
        }),
      });

      if (!res.ok) {
        let detail = "";
        try {
          const errBody = await res.json();
          detail = errBody?.detail || "";
        } catch {
          /* ignore non-JSON error bodies */
        }
        throw new Error(detail ? `Server error: ${detail}` : `Server error: ${res.status}`);
      }
      const data: { text: string; artifact_html?: string } = await res.json();

      let text = data.text || "";
      let artifactHtml = data.artifact_html || null;

      if (!artifactHtml) {
        const parsed = parseArtifact(text);
        text = parsed.text;
        artifactHtml = parsed.artifact;
      }

      const assistantMsg: Message = {
        role: "assistant",
        content: text,
        artifactHtml: artifactHtml ?? undefined,
      };
      setMessages((prev) => [...prev, assistantMsg]);

      if (artifactHtml && onArtifactGenerated) {
        onArtifactGenerated(artifactHtml);
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `**Error:** ${err instanceof Error ? err.message : "Unknown error"}.\n\nPlease ensure the backend is running.`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const fireQuickPrompt = (prompt: string) => {
    setInput(prompt);
    textareaRef.current?.focus();
  };

  return (
    <>
      {/* ── Fullscreen artifact overlay ── */}
      {expandedArtifact && (
        <div
          className="fixed inset-0 z-50 flex flex-col"
          style={{ background: "rgba(7,7,13,0.97)", backdropFilter: "blur(10px)" }}
        >
          <div
            className="flex items-center justify-between px-5 py-3.5 shrink-0"
            style={{ borderBottom: "1px solid var(--bg-border)" }}
          >
            <div className="flex items-center gap-2.5">
              {/* Abstract diamond decoration */}
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                <polygon points="6,0 12,6 6,12 0,6" stroke="var(--accent)" strokeWidth="1.2" fill="none"/>
              </svg>
              <span className="font-display text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                Visual Artifact
              </span>
            </div>
            <button
              onClick={() => setExpandedArtifact(null)}
              className="px-4 py-1.5 rounded-lg text-sm font-medium transition-all"
              style={{
                background: "var(--bg-elevated)",
                border: "1px solid var(--bg-border)",
                color: "var(--text-secondary)",
                cursor: "pointer",
              }}
            >
              ✕ Close
            </button>
          </div>
          <div className="flex-1 p-4 overflow-hidden">
            <ArtifactRenderer codeString={expandedArtifact} title="Visual Artifact" />
          </div>
        </div>
      )}

      <div className="flex flex-col h-full" style={{ background: "var(--bg-surface)" }}>

        {/* ── Messages ── */}
        <div className="flex-1 overflow-y-auto px-4 py-5 space-y-4">

          {/* Quick prompts — only when no user messages yet */}
          {messages.length === 1 && (
            <div className="grid grid-cols-2 gap-2 mt-1 mb-2">
              {QUICK_PROMPTS.map(({ label, icon, prompt }) => (
                <button
                  key={label}
                  onClick={() => fireQuickPrompt(prompt)}
                  className="text-left px-3 py-2.5 rounded-xl text-xs font-medium transition-all card-lift"
                  style={{
                    background: "var(--bg-elevated)",
                    border: "1px solid var(--bg-border)",
                    color: "var(--text-secondary)",
                    cursor: "pointer",
                  }}
                >
                  <span style={{ color: "var(--accent)", marginRight: 6 }}>{icon}</span>
                  {label}
                  <span style={{ color: "var(--text-muted)", marginLeft: 4 }}>→</span>
                </button>
              ))}
            </div>
          )}

          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex gap-2.5 ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}
            >
              {/* Avatar */}
              <div className="shrink-0 mt-0.5">
                {msg.role === "assistant" ? <AiAvatar /> : <UserAvatar />}
              </div>

              <div className="max-w-[88%] space-y-2">
                {/* Text bubble */}
                {msg.content && (
                  <div
                    className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                      msg.role === "user" ? "rounded-tr-sm" : "rounded-tl-sm"
                    }`}
                    style={
                      msg.role === "user"
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
                    <div
                      className="prose-chat"
                      dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.content) }}
                    />
                  </div>
                )}

                {/* ── Artifact preview card ── */}
                {msg.artifactHtml && (
                  <div
                    className="rounded-2xl overflow-hidden"
                    style={{
                      border: "1px solid var(--bg-border)",
                      background: "var(--bg-elevated)",
                      boxShadow: "0 8px 32px rgba(0,0,0,0.25)",
                    }}
                  >
                    {/* Scaled-down preview window — renders at 2× width, scaled to 50% */}
                    <div
                      className="relative overflow-hidden"
                      style={{ height: 260, background: "#0a0a12" }}
                    >
                      {/*
                        The iframe is rendered at 760px wide (typical desktop content width)
                        then CSS-scaled down to fit the chat panel (~340px), giving a crisp
                        thumbnail that actually shows the design rather than a crushed blob.
                      */}
                      <div
                        style={{
                          width: 760,
                          height: 520,
                          transformOrigin: "top left",
                          transform: "scale(0.447)",
                          pointerEvents: "none",
                          position: "absolute",
                          top: 0,
                          left: 0,
                        }}
                      >
                        <iframe
                          srcDoc={msg.artifactHtml}
                          sandbox="allow-scripts allow-same-origin"
                          className="border-0"
                          title="Artifact preview"
                          style={{ width: "100%", height: "100%", display: "block" }}
                        />
                      </div>

                      {/* Always-visible gradient footer with actions */}
                      <div
                        className="absolute inset-x-0 bottom-0 flex items-center justify-between px-3 py-2.5"
                        style={{
                          background: "linear-gradient(to top, rgba(7,7,13,0.95) 0%, rgba(7,7,13,0.6) 60%, transparent 100%)",
                        }}
                      >
                        <span
                          className="text-xs font-semibold tracking-wide uppercase"
                          style={{ color: "rgba(255,255,255,0.45)", letterSpacing: "0.07em" }}
                        >
                          ✦ Visual Artifact
                        </span>
                        <button
                          onClick={() => setExpandedArtifact(msg.artifactHtml!)}
                          className="flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg transition-all"
                          style={{
                            background: "var(--accent)",
                            color: "#fff",
                            cursor: "pointer",
                            boxShadow: "0 0 14px var(--accent-glow)",
                          }}
                        >
                          Full View ↗
                        </button>
                      </div>
                    </div>

                    {/* Action bar */}
                    <div
                      className="flex items-center gap-2 px-3 py-2.5"
                      style={{ borderTop: "1px solid var(--bg-border)" }}
                    >
                      <button
                        onClick={() => setExpandedArtifact(msg.artifactHtml!)}
                        className="flex-1 text-xs font-semibold py-1.5 rounded-lg transition-all text-center"
                        style={{
                          background: "var(--bg-surface)",
                          border: "1px solid var(--bg-border)",
                          color: "var(--text-secondary)",
                          cursor: "pointer",
                        }}
                      >
                        Open in Canvas
                      </button>
                      <button
                        onClick={() => {
                          const blob = new Blob([msg.artifactHtml!], { type: "text/html" });
                          const url = URL.createObjectURL(blob);
                          const a = document.createElement("a");
                          a.href = url;
                          a.download = "brand-asset.html";
                          a.click();
                          URL.revokeObjectURL(url);
                        }}
                        className="text-xs font-semibold px-3 py-1.5 rounded-lg transition-all"
                        style={{
                          background: "linear-gradient(135deg, #7c6dfa, #5b4de0)",
                          color: "#fff",
                          cursor: "pointer",
                          boxShadow: "0 0 10px rgba(124,109,250,0.3)",
                        }}
                      >
                        ↓ Save
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}

          {/* Loading indicator */}
          {loading && (
            <div className="flex gap-2.5">
              <AiAvatar />
              <div
                className="px-4 py-3 rounded-2xl rounded-tl-sm flex items-center gap-1.5"
                style={{
                  background: "var(--bg-elevated)",
                  border: "1px solid var(--bg-border)",
                }}
              >
                {[0, 150, 300].map((delay) => (
                  <span
                    key={delay}
                    className="w-1.5 h-1.5 rounded-full animate-bounce-slow"
                    style={{
                      background: "var(--accent)",
                      animationDelay: `${delay}ms`,
                      display: "inline-block",
                    }}
                  />
                ))}
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* ── Input area ── */}
        <div
          className="shrink-0 px-4 py-3"
          style={{ borderTop: "1px solid var(--bg-border)", background: "var(--bg-surface)" }}
        >
          <div
            className="flex gap-2 items-end rounded-2xl p-2 transition-all"
            style={{
              background: "var(--bg-elevated)",
              border: `1px solid ${loading ? "var(--accent)" : "var(--bg-border)"}`,
              boxShadow: loading ? "0 0 0 3px var(--accent-glow)" : "none",
            }}
          >
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask for strategy, visuals, copy, logos…"
              rows={1}
              className="flex-1 resize-none bg-transparent text-sm leading-relaxed py-1 px-2 border-0 outline-none"
              style={{
                color: "var(--text-primary)",
                minHeight: "24px",
                maxHeight: "120px",
                caretColor: "var(--accent)",
              }}
            />
            <button
              onClick={sendMessage}
              disabled={loading || !input.trim()}
              className="shrink-0 w-8 h-8 rounded-xl flex items-center justify-center transition-all"
              style={{
                background:
                  loading || !input.trim()
                    ? "var(--bg-border)"
                    : "linear-gradient(135deg, #7c6dfa, #5b4de0)",
                color: loading || !input.trim() ? "var(--text-muted)" : "#fff",
                cursor: loading || !input.trim() ? "not-allowed" : "pointer",
                boxShadow:
                  loading || !input.trim() ? "none" : "0 0 14px rgba(124,109,250,0.5)",
              }}
              title="Send message"
            >
              {/* Abstract arrow / send icon */}
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                <path d="M5 12h14M12 5l7 7-7 7" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>
          </div>
          <p className="mt-1.5 text-center text-[10px]" style={{ color: "var(--text-muted)" }}>
            Enter to send · Shift+Enter for new line
          </p>
        </div>
      </div>
    </>
  );
}
