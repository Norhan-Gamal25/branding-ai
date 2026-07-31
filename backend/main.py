import logging
import os
import re
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from crew import run_site_generation, run_chat

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Ethical Brand Studio API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response models ───────────────────────────────────────────────────

class SiteGenerationRequest(BaseModel):
    business_description: str


class SiteGenerationResponse(BaseModel):
    html: str


class ChatMessage(BaseModel):
    role: str          # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    user_message: str
    business_context: Optional[str] = ""
    chat_history: Optional[List[ChatMessage]] = []


class ChatResponse(BaseModel):
    text: str
    artifact_html: Optional[str] = None


# ── Helpers ─────────────────────────────────────────────────────────────────────

# Unicode script ranges used for language detection
_ARABIC_RE   = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+")
_FARSI_RE    = re.compile(r"[\uFB50-\uFDFF\uFE70-\uFEFF]+")   # Extended Arabic-Presentation forms (Farsi/Urdu)
_HEBREW_RE   = re.compile(r"[\u0590-\u05FF]+")
_CHINESE_RE  = re.compile(r"[\u4E00-\u9FFF\u3400-\u4DBF]+")
_JAPANESE_RE = re.compile(r"[\u3040-\u30FF\u31F0-\u31FF]+")
_KOREAN_RE   = re.compile(r"[\uAC00-\uD7AF\u1100-\u11FF]+")
_HINDI_RE    = re.compile(r"[\u0900-\u097F]+")
_THAI_RE     = re.compile(r"[\u0E00-\u0E7F]+")
_FRENCH_RE   = re.compile(
    r"\b(je|vous|nous|est|les|des|une|pour|avec|dans|sur|qui|que|pas|"
    r"plus|tout|bien|mais|aussi|même|très|comme|être|avoir|faire|aller|"
    r"dire|voir|vouloir|pouvoir|savoir|devoir|venir|prendre)\b",
    re.IGNORECASE,
)
_SPANISH_RE  = re.compile(
    r"\b(que|con|por|para|una|este|esta|estos|estas|pero|más|como|todo|"
    r"bien|aquí|también|entre|cuando|donde|cómo|qué|quién|muy|los|las|"
    r"del|sus|ser|estar|tener|hacer|poder|saber|querer|venir|decir)\b",
    re.IGNORECASE,
)


def detect_language(text: str) -> str:
    """
    Detect the primary language of *text* using Unicode script heuristics.
    Returns a BCP-47 language tag understood by _is_rtl() and the site-task prompt.
    Falls back to 'en' when the script is Latin and no strong signal is found.
    """
    # Non-Latin scripts — detected by Unicode block
    if _ARABIC_RE.search(text):
        return "fa" if _FARSI_RE.search(text) else "ar"
    if _HEBREW_RE.search(text):
        return "he"
    if _CHINESE_RE.search(text):
        return "zh"
    if _JAPANESE_RE.search(text):
        return "ja"
    if _KOREAN_RE.search(text):
        return "ko"
    if _HINDI_RE.search(text):
        return "hi"
    if _THAI_RE.search(text):
        return "th"
    # Latin-script languages — keyword frequency heuristic
    french_hits  = len(_FRENCH_RE.findall(text))
    spanish_hits = len(_SPANISH_RE.findall(text))
    if french_hits >= 3 and french_hits > spanish_hits:
        return "fr"
    if spanish_hits >= 3 and spanish_hits > french_hits:
        return "es"
    return "en"


def strip_think_tags(raw: str) -> str:
    """
    DeepSeek-R1 emits chain-of-thought inside <think>...</think> blocks.
    Strip them before returning anything to the user.
    """
    return re.sub(r"<think>[\s\S]*?</think>", "", raw, flags=re.IGNORECASE).strip()


def extract_artifact(raw: str) -> tuple[str, Optional[str]]:
    """
    Split the LLM response into (plain_text, html_artifact_or_None).
    Finds the FIRST ```html ... ``` fence block.
    Uses a non-greedy match with re.DOTALL to handle large HTML documents.
    Falls back to detecting a bare <!DOCTYPE html> document in the text.
    """

    # Strip DeepSeek chain-of-thought thinking tags first
    raw = strip_think_tags(raw)

    # Primary: ```html ... ``` fenced block
    pattern = r"```html\s*([\s\S]*?)```"
    match = re.search(pattern, raw, re.IGNORECASE | re.DOTALL)
    if match:
        artifact = match.group(1).strip()
        text = (raw[: match.start()] + raw[match.end() :]).strip()
        return text.strip(), artifact if artifact else None

    # Fallback: bare HTML document without fences (model forgot the fences)
    doc_match = re.search(r"(<!DOCTYPE html[\s\S]+</html>)", raw, re.IGNORECASE | re.DOTALL)
    if doc_match:
        artifact = doc_match.group(1).strip()
        text = (raw[: doc_match.start()] + raw[doc_match.end() :]).strip()
        return text.strip(), artifact

    return raw.strip(), None


# ── Endpoints ───────────────────────────────────────────────────────────────────

@app.post("/api/generate-site", response_model=SiteGenerationResponse)
async def generate_site(request: SiteGenerationRequest):
    if not request.business_description.strip():
        raise HTTPException(status_code=400, detail="business_description is required.")
    try:
        import asyncio  # noqa: PLC0415
        lang = detect_language(request.business_description)
        logger.info("Detected language '%s' for site generation", lang)
        html = await asyncio.to_thread(run_site_generation, request.business_description, lang)
        # Strip DeepSeek chain-of-thought tags if present
        html = strip_think_tags(html)
        # Strip accidental markdown fences if the LLM adds them
        html = re.sub(r"^```[a-z]*\n?", "", html.strip(), flags=re.IGNORECASE)
        html = re.sub(r"\n?```$", "", html.strip())
        return SiteGenerationResponse(html=html)
    except Exception as exc:
        logger.exception("Error in /api/generate-site")
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not request.user_message.strip():
        raise HTTPException(status_code=400, detail="user_message is required.")
    try:
        import asyncio  # noqa: PLC0415
        history = [m.model_dump() for m in (request.chat_history or [])]
        raw = await asyncio.to_thread(
            run_chat,
            request.user_message,
            request.business_context or "",
            history,
        )
        text, artifact = extract_artifact(raw)
        return ChatResponse(text=text, artifact_html=artifact)
    except Exception as exc:
        logger.exception("Error in /api/chat")
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/api/debug")
async def debug():
    """Diagnose missing environment variables — safe to expose (no secret values returned)."""
    groq_key   = os.environ.get("GROQ_API_KEY", "")
    ibm_key    = os.environ.get("IBM_API_KEY", "")
    ibm_proj   = os.environ.get("IBM_PROJECT_ID", "")
    return {
        "GROQ_API_KEY_set":    bool(groq_key),
        "GROQ_API_KEY_prefix": groq_key[:8] + "..." if groq_key else "MISSING",
        "IBM_API_KEY_set":     bool(ibm_key),
        "IBM_PROJECT_ID_set":  bool(ibm_proj),
        "LITELLM_CACHE":       os.environ.get("LITELLM_CACHE", "not set"),
        "LITELLM_LOCAL_CACHE": os.environ.get("LITELLM_LOCAL_CACHE", "not set"),
        "EXPORT_DIR":          os.environ.get("EXPORT_DIR", "not set"),
    }
