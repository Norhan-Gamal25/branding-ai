// lib/api.ts
// Typed API client for the Branding AI backend (lean architecture)

const BASE_URL = "/api/backend";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface GenerateSiteRequest {
  business_name: string;
  business_type: string;
  target_audience?: string;
}

export interface GenerateSiteResponse {
  status: "success" | "error";
  html_code: string;
  message: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatRequest {
  user_message:  string;
  business_name: string;
  business_type: string;
  chat_history?: ChatMessage[];
}

export interface ChatResponse {
  status: "success" | "error";
  reply: string;
}

// ── API helpers ───────────────────────────────────────────────────────────────

async function post<TReq, TRes>(path: string, body: TReq): Promise<TRes> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(
      (errData as { detail?: string }).detail ||
        `Request to ${path} failed with status ${res.status}`
    );
  }

  return res.json() as Promise<TRes>;
}

// ── Public API functions ──────────────────────────────────────────────────────

/**
 * Generate a landing page HTML string for the given business.
 * Calls POST /api/generate-site on the backend.
 */
export async function generateSite(
  input: GenerateSiteRequest
): Promise<GenerateSiteResponse> {
  return post<GenerateSiteRequest, GenerateSiteResponse>(
    "/api/generate-site",
    input
  );
}

/**
 * Send a message to the Halal Growth Assistant.
 * Calls POST /api/chat on the backend.
 */
export async function sendChatMessage(
  input: ChatRequest
): Promise<ChatResponse> {
  return post<ChatRequest, ChatResponse>("/api/chat", input);
}

/**
 * Liveness check.
 */
export async function healthCheck(): Promise<{ status: string }> {
  const res = await fetch(`${BASE_URL}/health`);
  return res.json();
}
