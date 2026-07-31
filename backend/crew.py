"""
crew.py
=======
Two-agent architecture for Branding AI.

Agent 1 â€” PlatformEngineer (The Builder)
    Generates complete, RTL-aware, brand-accurate HTML landing pages.
    Uses Tailwind CSS + Phosphor Icons â€” zero raw SVG drawing.
    A gold-standard HTML scaffold is injected as a few-shot reference so the
    LLM anchors to professional structure, not a blank slate.
    Validates output with a Pydantic model before returning.

Agent 2 â€” EthicalStrategyDirector (The Thinker)
    Deep-reasoning brand strategist, creative director, and ethics guardian.
    Answers strategy questions, generates visual HTML artifacts,
    colour palettes, taglines, and marketing plans.
    Uses Tailwind CSS + Phosphor Icons for all visuals â€” no hand-drawn SVG.
    Hard ethical guardrails: refuses fake scarcity, FOMO, and deceptive copy.

LANGUAGE RULE (both agents):
    Detect the user's prompt language and respond entirely in that language.
    RTL languages (Arabic, Hebrew, Farsi, â€¦) â†’ <html lang="ar" dir="rtl">.

Model fallback ladder:
    Groq models are tried first in priority order (each has a SEPARATE daily
    token pool). Then optional free OpenRouter / HuggingFace models (skipped
    automatically when their API key is missing). OpenAI is the final safety
    net â€" reliable, no daily token cap.
"""

from __future__ import annotations

import logging
import os
import re
import time

# Disable LiteLLM prompt-caching globally.
# Groq rejects any message containing `cache_breakpoint` that LiteLLM >=1.57
# injects automatically. This must be set before litellm is imported.
os.environ.setdefault("LITELLM_LOCAL_CACHE", "false")
os.environ.setdefault("LITELLM_CACHE", "false")

import litellm  # noqa: E402
litellm.cache = None

from crewai import Agent, Crew, LLM, Process, Task
from pydantic import BaseModel, field_validator

import crewai.llms.cache as _crew_cache  # noqa: E402

# CrewAI >= 1.15 injects `cache_breakpoint: True` into system/user messages to
# mark prompt-caching boundaries. Groq rejects that boolean field outright
# ("property 'cache_breakpoint' is unsupported"), so neutralise the marker —
# the request stays valid and prompt caching is simply skipped. On older
# crewai (0.x) this module doesn't exist, so the patch is a no-op.
try:
    _crew_cache.mark_cache_breakpoint = lambda message: message  # noqa: E731
except AttributeError:
    pass

logger = logging.getLogger(__name__)

# â”€â”€ RTL language support â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

_RTL_LANGUAGES = frozenset({"ar", "he", "fa", "ur", "ps", "ug", "yi", "ku", "dv"})


def _is_rtl(language: str) -> bool:
    return language.split("-")[0].lower() in _RTL_LANGUAGES


# â”€â”€ Shared icon / UI constants â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

_PHOSPHOR_LINK = (
    '<link rel="stylesheet" type="text/css" '
    'href="https://unpkg.com/@phosphor-icons/web@2.1.1/src/regular/style.css" />'
)

_PHOSPHOR_USAGE_EXAMPLE = (
    'Example icon usage: <i class="ph ph-leaf text-4xl"></i>  '
    '<i class="ph ph-star text-3xl"></i>  '
    '<i class="ph ph-rocket text-3xl"></i>  '
    '<i class="ph ph-shield-check text-3xl"></i>  '
    '<i class="ph ph-lightning text-3xl"></i>'
)

_SVG_BAN = (
    "â›” ABSOLUTE BAN ON RAW SVG DRAWING: You MUST NOT write <svg>, <path>, <circle>, "
    "<polygon>, <rect>, <line>, or any other raw SVG shape tags from scratch. "
    "LLMs cannot draw accurate SVGs. Use Phosphor Icons for ALL icons, logos, and "
    "graphic elements instead. NO EXCEPTIONS."
)

# Compact palette table (~150 tokens vs old ~800-token prose).
_TAILWIND_EXCELLENCE = (
    "Pick ONE palette for this brand industry (register ALL hex codes in :root{} AND tailwind.config):\n"
    "Luxury/Jewellery: #0a0a1a #c9a84c #f5f0e8 | Wellness/Organic: #1a3a2a #7aab8a #f2ebe0 #c4714a\n"
    "Tech/SaaS: #070714 #5c4df5 #00e5ff | Food/Cafe: #1c1008 #e8602c #fdf6ec #f0b429\n"
    "Beauty/Skincare: #3d1a2a #b07080 #fce8e8 #d4af7a | Sport/Fitness: #0f0f0f #b0f030 #3a3a4a\n"
    "Real Estate: #1a1f2e #8a6a42 #f4f1ec | Education: #0d3349 #e8a820 #ffffff #4db8e8\n"
    "Finance/Legal: #151520 #1a3a8f #c0c8d8 #c9a44a | Medical: #0a1628 #00b8d9 #475569\n"
    "Artisan/Heritage: #3b1f0e #a0522d #f8f0e3 #5a6e2e\n"
    "Rules: hero=darkest base+gradient overlay; CTA=vivid accent+glow box-shadow; "
    "cards=glassmorphism rgba(R,G,B,0.08) backdrop-blur(12px); "
    "nav=sticky rgba(R,G,B,0.88) blur(18px); NEVER use Tailwind default colours; "
    "alternate section backgrounds dark/surface."
)


# â"€â"€ Gold-standard HTML scaffold (professional design-system brief) â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
# Rich but token-budgeted design-system brief (~2,800 tokens vs the original
# 14,867-token monster). Gives the agent concrete professional guidance that
# still fits inside Groq's free-tier TPM limits (llama-3.3-70b = 12k TPM).
# Prompt ~3.2k + output 6k = 9.2k < 12k ✓

_GOLD_SCAFFOLD = """\
DESIGN SYSTEM — THIS IS YOUR SPECIFICATION. Follow it exactly.

=== 1. DOCUMENT HEAD (must contain all of these) ===
- <meta charset="UTF-8"> + <meta name="viewport" content="width=device-width, initial-scale=1.0">
- Tailwind CDN: <script src="https://cdn.tailwindcss.com"></script>
- Phosphor Icons CDN: <link rel="stylesheet" href="https://unpkg.com/@phosphor-icons/web@2.1.1/src/regular/style.css"/>
- <style> block containing:
    * Google Fonts @import — pick 2 fonts that DEFINE the brand personality
      (display font for headings, body font for text). Real Google Fonts names only.
    * :root{} CSS variables: --base, --surface, --card, --primary, --secondary,
      --text-light, --text-muted AND their RGB triplets (--primary-rgb: R,G,B) for rgba()
    * All custom classes from section 4
- <script> tailwind.config block: map colors {base, surface, card, primary,
  secondary} to the CSS vars, set fontFamily {display, body}

=== 2. COLOUR (pick ONE palette, commit fully) ===
Choose from this industry table and register every hex in :root{} AND tailwind.config:
  Luxury/Jewellery: #0a0a1a #c9a84c #f5f0e8   |  Wellness/Organic: #1a3a2a #7aab8a #f2ebe0 #c4714a
  Tech/SaaS:       #070714 #5c4df5 #00e5ff    |  Food/Cafe:       #1c1008 #e8602c #fdf6ec #f0b429
  Beauty/Skincare: #3d1a2a #b07080 #fce8e8 #d4af7a | Sport/Fitness: #0f0f0f #b0f030 #3a3a4a
  Real Estate:     #1a1f2e #8a6a42 #f4f1ec    |  Education:       #0d3349 #e8a820 #ffffff #4db8e8
  Finance/Legal:   #151520 #1a3a8f #c0c8d8 #c9a44a | Medical:     #0a1628 #00b8d9 #475569
  Artisan/Heritage:#3b1f0e #a0522d #f8f0e3 #5a6e2e
Rules: hero = darkest base + gradient overlay; CTA = vivid accent + glow box-shadow;
cards = glassmorphism rgba(R,G,B,0.08) + backdrop-blur(12px); nav = sticky
rgba(R,G,B,0.88) + blur(18px); NEVER use Tailwind default colours; alternate
section backgrounds dark/surface so the page has rhythm.

=== 3. SECTION FLOW (exactly 7 sections, each a DIFFERENT background) ===
1. STICKY NAV: glass-blur bar. Left: Phosphor icon logo + brand name + small
   tagline. Right: 3 in-page anchors + .btn-primary CTA.
2. HERO (#hero) .section-dark: min-h-screen, radial CSS glow behind content,
   eyebrow pill, h1 with .g-text (clamp 2.8rem→4.5rem, weight 800), one-line
   subheadline, .btn-primary CTA + optional subtle secondary link.
3. TRUST BAR .section-surface: flex row of 3-4 items = Phosphor icon + bold
   stat + small label. Draw ONLY from the business description (real facts).
4. ABOUT (#about) .section-dark: 2-col grid — left: eyebrow + h2 + 2 short
   paragraphs; right: 2×2 grid of value .cards (icon + name + one line).
5. FEATURES (#features) .section-surface: centered heading + auto-fit grid of
   6 .cards, each = 52px icon box + h3 + 2-sentence description.
6. CTA/CONTACT (#contact) .section-dark: radial glow, large Phosphor icon
   (48px), h2.g-text, short paragraph, mailto .btn-primary button.
7. FOOTER .section-surface: brand icon + name + tagline + © current year.

=== 4. CUSTOM CSS CLASSES (define ALL of these in <style>) ===
(compute real R,G,B decimals from your chosen hex palette)
  .g-text       background:linear-gradient(120deg,var(--primary),var(--secondary)); -webkit-background-clip:text; color:transparent
  .card         background:rgba(R,G,B,0.08); backdrop-filter:blur(12px); border:1px solid rgba(R,G,B,0.15); border-radius:20px; transition:transform .25s
  .card:hover   transform:translateY(-4px); box-shadow:0 16px 48px rgba(R,G,B,0.15)
  .btn-primary  border-radius:50px; background:var(--primary); box-shadow:0 0 32px rgba(R,G,B,0.45); hover:translateY(-2px)
  nav           position:sticky; top:0; background:rgba(R,G,B,0.88); backdrop-filter:blur(18px)
  .section-dark    background:var(--base)
  .section-surface background:var(--surface)
  radial glow   position:absolute; background:radial-gradient(ellipse 80% 60% at 50% 40%, rgba(R,G,B,0.18) 0%, transparent 65%)
  Hex→RGB example: #c9a84c = 201,168,76

=== 5. QUALITY BAR (what "professional" means here) ===
- Generous, consistent spacing (py-24/py-32), one coherent radius (16-24px),
  soft shadows, subtle hover motion. No cramped or default-browser styling.
- Strong typography contrast between display and body fonts.
- Every section COMPLETE with real copy in the detected language — no Lorem
  ipsum, no placeholder text, no empty sections, no fake testimonials/ratings.
- Icons ONLY via <i class="ph ph-NAME">. NEVER <svg>, <path>, <circle>,
  <img>, or external image URLs.
- RTL languages: <html lang="..." dir="rtl">, text right-aligned, flex/grid
  direction mirrored so the layout reads naturally right-to-left.
- If any copy is required, invent it in the detected language, brand-accurate.

Output ONLY the complete HTML starting with <!DOCTYPE html>. No markdown fences, no commentary.
"""


# â”€â”€ Pydantic output validator â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class SiteOutput(BaseModel):
    """
    Validated output from the PlatformEngineer agent.
    Ensures the LLM always returns a proper HTML document â€”
    salvages accidental prose wrappers if the model forgets the instruction.
    """
    html_code: str

    @field_validator("html_code")
    @classmethod
    def must_be_html(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("html_code must not be empty")
        lower = stripped.lower()
        if not (lower.startswith("<!doctype") or lower.startswith("<html")):
            # Attempt to salvage â€” find the first valid HTML block
            match = re.search(
                r"(<!DOCTYPE\s+html[\s\S]*|<html[\s\S]*)", stripped, re.IGNORECASE
            )
            if match:
                return match.group(1).strip()
            raise ValueError("html_code does not contain a valid HTML document")
        return stripped


# â"€â"€ Model priority lists â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
# Each entry: (model_id, max_tokens)
# Groq models each have SEPARATE daily token pools â€" exhausting one doesn't
# affect the others. OpenAI is last: reliable, no daily token cap.

# Prompt with the rich scaffold is ~3,600 tokens (scaffold 2,800 + system ~800).
# Budget for the strongest Groq model (llama-3.3-70b-versatile, 12k TPM):
#   3600 (prompt) + 5000 (output) = 8600 < 12,000 ✓
# Every Groq model has a SEPARATE daily token pool — exhausting one doesn't
# affect the others. OpenRouter + HuggingFace are optional free-tier fallbacks
# (skipped automatically when their API key is missing). OpenAI stays last:
# reliable, no daily token cap.
_SITE_MODELS = [
    ("groq/llama-3.3-70b-versatile",      5000),  # 12k TPM pool — primary
    ("groq/openai/gpt-oss-120b",          5000),  # separate pool, strongest new Groq model
    ("groq/qwen/qwen3.6-27b",             4000),  # separate pool
    ("openrouter/google/gemma-4-26b-a4b-it:free", 6000),  # free on OpenRouter (needs OPENROUTER_API_KEY)
    ("openrouter/poolside/laguna-s-2.1:free",   5000),  # free on OpenRouter (backup)
    ("huggingface/meta-llama/Llama-3.3-70B-Instruct", 5000),  # needs HF_API_KEY
    ("groq/llama-3.1-8b-instant",         2000),  # small-pool safety net
    ("openai/gpt-4o-mini",                7000),  # no daily cap — last resort, keeps quality
]

_CHAT_MODELS = [
    ("groq/llama-3.3-70b-versatile",      5000),
    ("groq/openai/gpt-oss-120b",          5000),
    ("groq/qwen/qwen3.6-27b",             4000),
    ("openrouter/google/gemma-4-26b-a4b-it:free", 6000),
    ("openrouter/poolside/laguna-s-2.1:free",   5000),
    ("huggingface/meta-llama/Llama-3.3-70B-Instruct", 5000),
    ("groq/llama-3.1-8b-instant",         2000),
    ("openai/gpt-4o-mini",                5000),
]


class _ProviderUnavailable(Exception):
    """Raised when a provider's API key is missing so the fallback loop skips it."""


def _build_llm(model: str, max_tokens: int) -> LLM:
    """
    Build a crewai LLM instance for the given model_id.

    Supported providers (detected by prefix):
      groq/        -> GROQ_API_KEY
      openai/      -> OPENAI_API_KEY
      openrouter/  -> OPENROUTER_API_KEY
      huggingface/ -> HF_API_KEY

    Raises _ProviderUnavailable (skipped by the fallback loop) when the
    provider's API key is not configured.
    """
    if model.startswith("openrouter/"):
        key = os.environ.get("OPENROUTER_API_KEY", "").strip()
        if not key:
            raise _ProviderUnavailable(
                "OPENROUTER_API_KEY not set — skipping OpenRouter fallback"
            )
        logger.info("Using OpenRouter fallback model=%s (max_tokens=%d)", model, max_tokens)
        return LLM(
            model=model,
            api_key=key,
            temperature=0.6,
            max_tokens=max_tokens,
            caching=False,
        )

    if model.startswith("huggingface/"):
        key = os.environ.get("HF_API_KEY", "").strip()
        if not key:
            raise _ProviderUnavailable(
                "HF_API_KEY not set — skipping HuggingFace fallback"
            )
        logger.info("Using HuggingFace fallback model=%s (max_tokens=%d)", model, max_tokens)
        return LLM(
            model=model,
            api_key=key,
            temperature=0.6,
            max_tokens=max_tokens,
            caching=False,
        )

    if model.startswith("openai/"):
        key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not key:
            raise _ProviderUnavailable(
                "OPENAI_API_KEY not set — skipping OpenAI fallback"
            )
        logger.info("Using OpenAI fallback model=%s (max_tokens=%d)", model, max_tokens)
        return LLM(
            model=model,
            api_key=key,
            temperature=0.6,
            max_tokens=max_tokens,
            caching=False,
        )

    groq_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not groq_key:
        raise _ProviderUnavailable(
            "GROQ_API_KEY is not set — skipping Groq model"
        )
    return LLM(
        model=model,
        api_key=groq_key,
        temperature=0.6,
        max_tokens=max_tokens,
        caching=False,
    )


def _is_skippable_error(err_str: str) -> bool:
    """
    Return True for errors that mean 'this model is unavailable â€” try the next one'.
    Covers: rate limits, decommissioned/deleted models, and invalid model IDs.
    """
    markers = (
        # Rate limit
        "rate_limit_exceeded", "RateLimitError", "429", "Too Many Requests",
        # Model decommissioned / not found
        "decommissioned", "model_decommissioned", "does not exist",
        "model not found", "invalid model", "400", "Bad Request",
        "No such model", "not supported",
        # Quota / payment (OpenRouter free models can 402 when no credits)
        "402", "payment required", "insufficient quota", "quota exceeded",
        "exceeded_current_quota_error",
    )
    low = err_str.lower()
    return any(m.lower() in low for m in markers)


def _run_with_fallback(task_factory, model_list: list) -> str:
    """
    Try each model in model_list in order.
    Skips to the next model on rate limits, decommissioned/invalid models, and
    providers whose API key is not configured.
    Raises RuntimeError only if every model in the list fails.
    """
    last_err = None
    for model, max_tokens in model_list:
        try:
            logger.info("Trying model: %s (max_tokens=%d)", model, max_tokens)
            llm = _build_llm(model, max_tokens)
            task, agent = task_factory(llm)
            crew = Crew(
                agents=[agent],
                tasks=[task],
                process=Process.sequential,
                verbose=False,
            )
            result = crew.kickoff()
            logger.info("Success with model: %s", model)
            return str(result)
        except _ProviderUnavailable as e:
            logger.warning(
                "Skipping %s (%s) — trying next model.",
                model, e,
            )
            last_err = e
            continue
        except Exception as e:
            err_str = str(e)
            if _is_skippable_error(err_str):
                logger.warning(
                    "Skipping %s (%s) — trying next model.",
                    model, err_str[:120],
                )
                last_err = e
                time.sleep(0.3)
                continue
            # Unexpected error (auth failure, network error, etc.) — re-raise immediately
            raise
    raise RuntimeError(
        f"All models exhausted. Last error: {last_err}"
    )


# â”€â”€ Agent 1: PlatformEngineer â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _make_platform_engineer(llm: LLM) -> Agent:
    return Agent(
        role="PlatformEngineer â€” Senior Frontend Engineer & Brand UI Specialist",
        goal=(
            "Generate a stunning, pixel-perfect, conversion-optimised single-page HTML landing "
            "page for the business described. The output must be a complete, self-contained HTML "
            "file using Tailwind CSS, Phosphor Icons, and Google Fonts â€” production-ready and "
            "visually indistinguishable from a professionally designed website. "
            "Output ONLY the raw HTML starting with <!DOCTYPE html> â€” zero explanation.\n\n"
            f"{_SVG_BAN}"
        ),
        backstory=(
            "Expert frontend engineer and UI/UX designer. Uses Tailwind CSS, Phosphor Icons (<i class='ph ph-*'>), Google Fonts. Writes RTL layouts (dir=rtl) for Arabic/Hebrew/Farsi. Invents a unique brand palette per project — never reuses colours. Never uses Lorem ipsum, placeholder images, or raw SVG."
        ),
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )


def make_site_task(
    business_description: str,
    agent: Agent,
    language: str = "en",
) -> Task:
    rtl = _is_rtl(language)
    lang_attr = f'lang="{language}"'
    dir_attr  = 'dir="rtl"' if rtl else 'dir="ltr"'
    html_tag  = f'<html {lang_attr} {dir_attr}>'
    rtl_note  = (
        "CRITICAL â€” RIGHT-TO-LEFT LAYOUT: This page is in an RTL language. "
        f"The opening tag MUST be {html_tag}. "
        "All text must be right-aligned, flex rows reversed (flex-row-reverse), "
        "and the entire layout mirrored for natural RTL reading. "
        "In the scaffold, swap leftâ†”right in all flex/grid layout hints."
        if rtl else
        f"Set {html_tag} on the root element for correct language and direction support."
    )

    return Task(
        description=(
            f"Language: {language}. {rtl_note}\n"
            f"No SVG tags. Use Phosphor Icons only (<i class=\'ph ph-*\'>).\n\n"
            f"{_GOLD_SCAFFOLD}\n"
            f"Business:\n{business_description}\n\n"
            "Output ONLY the raw HTML. No markdown fences. Start with <!DOCTYPE html>."
        ),
        agent=agent,
        expected_output=(
            f"Complete <!DOCTYPE html> with {html_tag}, all 7 sections per scaffold, "
            f"Tailwind CSS + Phosphor Icons, unique brand palette, all copy in \'{language}\', "
            "no SVG, no Lorem ipsum, no fake reviews."
        ),
    )


def run_site_generation(
    business_description: str,
    language: str = "en",
) -> str:
    def factory(llm):
        agent = _make_platform_engineer(llm)
        task  = make_site_task(business_description, agent, language)
        return task, agent

    raw = _run_with_fallback(factory, _SITE_MODELS)
    # Validate and sanitise via Pydantic â€” salvages accidental markdown wrapping
    return SiteOutput(html_code=raw).html_code


# â”€â”€ Agent 2: EthicalStrategyDirector â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _make_ethical_strategy_director(llm: LLM) -> Agent:
    return Agent(
        role="EthicalStrategyDirector â€” Brand Strategist, Creative Director & Ethics Guardian",
        goal=(
            "Act as a world-class brand strategist, storyteller, and creative director. "
            "Deliver deeply insightful, actionable, and complete responses to every question. "
            "IRON RULE: Every response is 100% self-contained â€” NEVER write 'as listed above', "
            "'strategies above', 'see below', 'as mentioned', or any phrase implying content "
            "exists outside your current reply. Write EVERY strategy, step, and recommendation "
            "IN FULL inside this single message.\n\n"
            "When a visual asset is requested â€” logo, social post, palette, business card â€” "
            "produce a polished, self-contained HTML document at the quality level of work "
            "produced by the world's top brand identity studios (Pentagram, Wolff Olins, "
            "Landor, Collins). Use Tailwind CSS, CSS shapes (border-radius, clip-path, "
            "layered divs, transforms), and Phosphor Icons. "
            "Wrap the ENTIRE HTML document in ```html\\n...\\n``` fences. "
            "NO raw hand-drawn SVG paths ever.\n\n"
            f"{_SVG_BAN}"
        ),
        backstory=(
            "World-class brand strategist and creative director. Produces expert strategy, logos (CSS div shapes + Phosphor icon nucleus, full identity system), colour palettes, social content packs, and business cards. Never uses raw SVG. Responds in the user's language. Refuses fake scarcity/FOMO and offers ethical alternatives."
        ),
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )


# â”€â”€ Per-artifact-type gold scaffolds â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# These are injected into make_chat_task when the message requests that artifact.
# Concrete templates produce dramatically better output than written rules alone.

_ARTIFACT_LOGO = """
=== GOLD-STANDARD LOGO IDENTITY SYSTEM ===
Produce ONE self-contained HTML page (wrapped in ```html...``` fences) presenting a
world-class identity system in the spirit of Google, Microsoft, Amazon, Airbnb, or Nike.

STUDY HOW THE GREATS CONSTRUCT MARKS:
  Google:    pure wordmark — the LOGO IS THE TYPOGRAPHY; each letter a distinct
             hue, friendly rounded geometric sans (Product Sans-like).
  Microsoft: symbol-only — 4 flat squares in a 2x2 grid, each a brand colour,
             sitting at staggered 0/25/50/75% baselines.
  Amazon:    bold humanist-sans wordmark + a smile ARC beneath from first to last
             letter (a-to-z). The arc is the entire brand idea.
  Airbnb:    custom rounded symbol (inverted heart) + rounded wordmark — symbol and
             type share one rounded-corner design language.
  Apple:     pure geometric symbol (bitten circle) + clean sans wordmark.

=== SIGNATURE MARK RECIPES — build the symbol with these, NEVER an icon-in-a-circle ===
R1 Microsoft-tile: 4 equal divs in a 2x2 grid (16px gap), each a DIFFERENT brand
   colour, border-radius 4px, subtle 2px darker bottom edge for depth.
R2 Google-wordmark: brand name as one wordmark where EACH LETTER (or key syllable)
   is a <span> with its own hue from the palette, in a rounded geometric sans
   (Poppins / Outfit / Plus Jakarta Sans). Big, bold, immaculate tracking.
R3 Amazon-smile: bold wordmark + ARC underneath — div { width:60%; height:14px;
   border-bottom:4px solid var(--primary); border-radius:0 0 24px 24px;
   margin:2px auto 0; } The arc spans under the whole name.
R4 Geometric mark: layer 2-3 CSS shapes (rotated square + circle + ring) via
   transform / box-shadow / border / clip-path so the SHAPE is the hero. A
   Phosphor icon may sit at the CENTRE as the semantic nucleus.
R5 Two-tone badge: rounded-square (radius 26%) split diagonally (rotated overlay
   div or linear-gradient), Phosphor icon or initial overlaid, soft offset shadow.

=== THE PRESENTATION (one HTML page, 4 sections) ===
1. SYMBOL MARK alone at 4 sizes (120/64/40/18px favicon) on a neutral card —
   proves scalability. The symbol MUST be a genuinely CONSTRUCTED mark from a
   recipe above. NEVER a Phosphor icon pasted into a plain circle. NEVER
   initials in a rounded box.
2. WORDMARK alone — a Google Fonts typeface with real personality; show it
   dark-on-light AND light-on-dark; wrap ONE letter/syllable in
   <span class="accent-letter"> for a signature colour moment. Set
   letter-spacing (tight -0.03em or wide 0.06em) and weight 700-900 deliberately.
3. PRIMARY LOCKUP — symbol + wordmark side-by-side on THREE panels: dark base /
   white / brand-primary colour. Under the wordmark on the dark panel put the
   tagline (uppercase, tracked).
4. COLOUR SYSTEM BAR — Primary / Secondary / Accent / Base-Dark swatches with hex
   codes + usage labels (CTAs / gradient pair / pop accent / base type).

=== TYPOGRAPHY EXCELLENCE (what makes Google/Amazon read "designed") ===
- Pick a display font with real personality for the industry: honey/heritage →
  Marcellus, Cormorant Garamond; tech → Space Grotesk, Sora; playful → Baloo 2,
  Fredoka; fashion → Fraunces, Italiana. Body font: a clean sans.
- Wordmark techniques: gradient text (background-clip:text), per-letter hues,
  1px outlined (text-stroke) letter, or a coloured full-stop accent glyph.
- Arabic/RTL brands: use a Google Arabic font (Cairo, Tajawal, Reem Kufi, Amiri,
  Aref Ruqaa) and keep <html dir="rtl">.

=== QUALITY BAR ===
- Neutral canvas (e.g. #f2f2f5, not plain white); consistent radii and spacing.
- :root CSS vars for every colour + RGB triplets. Tailwind CDN + Phosphor Icons
  CSS + Google Fonts @import in <head>; tailwind.config mapped to the vars.
- Replace EVERY placeholder with real brand values from the business context.
- Output the ENTIRE HTML inside ```html ... ``` fences. No raw <svg>/<path> tags.
"""

_ARTIFACT_PALETTE = """
=== GOLD-STANDARD COLOUR PALETTE ===
Produce an HTML page (wrapped in ```html...``` fences) that presents the brand palette
the way a senior designer would:
- Page: neutral canvas background (#f8f8f8), a small uppercase section label
  ("Brand Identity System"), a display-font title ("BRAND — Colour Palette"),
  and a one-line positioning sentence.
- PRIMARY ROW: 4 equal swatches (Primary / Secondary / Accent / Background), each a
  160px rounded card with a glass label strip (backdrop-blur) showing the hex code in
  monospace + a usage label (CTAs / gradient pair / pop accent / page bg).
- TEXT/NEUTRAL ROW: 3 shorter swatches — Heading Text, Body Text, Surface/Card.
- TYPOGRAPHY IN CONTEXT panel: display-font headline in the heading colour + body-font
  paragraph, proving the palette works in real use.
- Fonts: 2 Google Fonts via @import (display + body). Tailwind CDN + Phosphor Icons CSS
  in <head>. Register every hex in :root{} + tailwind.config.
Pick the palette from the industry table (luxury / wellness / tech / food / beauty /
sport / real estate / education / finance / medical / artisan) and label each swatch
with its role. Fill every placeholder with real brand values.
Output the ENTIRE HTML inside ```html ... ``` fences. No raw SVG.
"""

_ARTIFACT_SOCIAL = """
=== SOCIAL MEDIA CONTENT PACK — TEXT + PHOTO GUIDE ===
You are a world-class social media strategist and copywriter.
For social media post requests deliver a plain-text CONTENT PACK — NO HTML, no code fences.
Use exactly this structure, in the user's language:

## Post 1 — Hero / Brand Statement
Headline: [punchy 5-10 word headline]
Body copy: [2-4 sentences — bold brand voice, core value proposition]
Hashtags: #tag1 #tag2 #tag3 #tag4 #tag5

Photo to find: [specific visual description: subject, setting, lighting, mood, colour
tone, composition — plus 2-3 search keywords for Unsplash/Pexels. Example: "Close-up of
golden honey dripping from a wooden dipper onto white marble, warm natural sidelight,
shallow depth of field, amber tones — search 'honey drip marble'."]

## Post 2 — Value / Feature
Headline: [educational or benefit-focused]
Body copy: [2-4 sentences — highlight one key benefit or feature]
Hashtags: #tag1 #tag2 #tag3 #tag4 #tag5
Photo to find: [specific visual description with search terms]

## Post 3 — Community / Story
Headline: [warm, personal, human-centred]
Body copy: [2-4 sentences — authentic, community-first tone, no FOMO]
Hashtags: #tag1 #tag2 #tag3 #tag4 #tag5
Photo to find: [specific visual description with search terms]

## Posting Tips
[2-3 short tips specific to this brand's audience and industry — best time to post,
caption length, platform-specific advice (Instagram vs LinkedIn vs Facebook).]

Replace every placeholder with real brand-specific content from the business context.
Write entirely in the user's language. No HTML. No code fences. Pure text.
"""

_ARTIFACT_BIZCARD = """
=== GOLD-STANDARD BUSINESS CARD ===
Produce an HTML page (wrapped in ```html...``` fences) showing BOTH sides of a
professional business card at 700x400px each (2x the real 3.5x2in size):
- FRONT (dark base bg): radial brand glow in the top-left corner; a logo mark
  (46px gradient rounded square with Phosphor icon + glow shadow) + brand name in the
  display font (800) + uppercase tagline below it; then the person block: name
  (1.35rem, 800), job title in the brand colour, and 3 contact rows using Phosphor
  envelope/phone/globe icons with email / phone / website.
- BACK (brand-primary bg): large translucent Phosphor icon (48px, white at 20%
  opacity), brand name in white display font (1.7rem, 900), and the full tagline in
  spaced uppercase at 55% white.
- Card styling: width 700px; height 400px; border-radius 20px; deep drop shadow
  (0 24px 64px rgba(0,0,0,.3)).
- Fonts: display + body Google Fonts via @import; Tailwind CDN + Phosphor Icons CSS in
  <head>; :root vars (--p/--s/--b/--tl) with hex values AND RGB triplets for rgba().
Fill every placeholder (logo icon, brand name, tagline, person name, title, email,
phone, website, hex codes) with real brand values.
Output the ENTIRE HTML inside ```html ... ``` fences. No raw SVG.
"""


def _detect_artifact_type(message: str) -> str:
    """
    Detect which visual artifact type the user is requesting so the correct
    gold-standard scaffold can be injected into the task description.
    Returns one of: 'logo', 'palette', 'social', 'bizcard', 'general'.
    """
    m = message.lower()
    if any(w in m for w in ("logo", "mark", "brand mark", "monogram", "Ø´Ø¹Ø§Ø±", "Ù„ÙˆØºÙˆ")):
        return "logo"
    if any(w in m for w in ("palette", "colour", "color", "colors", "colours", "swatch",
                             "Ø£Ù„ÙˆØ§Ù†", "Ù„ÙˆÙ†", "palette")):
        return "palette"
    if any(w in m for w in ("social", "post", "instagram", "facebook", "tweet", "Ù…Ù†Ø´ÙˆØ±",
                             "Ø³ÙˆØ´ÙŠØ§Ù„", "ØªØºØ±ÙŠØ¯Ø©")):
        return "social"
    if any(w in m for w in ("business card", "carte", "bcard", "ÙƒØ±Øª", "Ø¨Ø·Ø§Ù‚Ø© Ø¹Ù…Ù„",
                             "visiting card")):
        return "bizcard"
    return "general"


def make_chat_task(
    user_message: str,
    business_context: str,
    chat_history: list,
    agent: Agent,
) -> Task:
    history_text = ""
    if chat_history:
        formatted = []
        for msg in chat_history[-8:]:  # last 4 turns
            role    = msg.get("role", "user").capitalize()
            content = msg.get("content", "")[:600]
            formatted.append(f"{role}: {content}")
        history_text = "\n".join(formatted) + "\n\n"

    # Inject the matching scaffold only when the user is asking for a visual
    artifact_type = _detect_artifact_type(user_message)
    scaffold_block = ""
    if artifact_type == "logo":
        scaffold_block = _ARTIFACT_LOGO
    elif artifact_type == "palette":
        scaffold_block = _ARTIFACT_PALETTE
    elif artifact_type == "social":
        scaffold_block = _ARTIFACT_SOCIAL
    elif artifact_type == "bizcard":
        scaffold_block = _ARTIFACT_BIZCARD

    return Task(
        description=(
            "â˜… CRITICAL LANGUAGE INSTRUCTION â˜…\n"
            "Detect the language of the user's message below. Your ENTIRE response â€” "
            "every word of advice, every HTML artifact label, every heading â€” MUST be "
            "written in that same language. Do NOT default to English unless the user "
            "wrote in English. "
            "If the language is Arabic or any RTL language, you MUST wrap any HTML you "
            "generate in <html lang=\"ar\" dir=\"rtl\"> and mirror all layouts for "
            "right-to-left reading.\n\n"
            "ðŸš¨ ETHICS CHECKPOINT ðŸš¨\n"
            "Before responding, check whether the user is asking you to create fake scarcity, "
            "panic-buying messaging, artificial FOMO, or deceptive stock-level claims. "
            "If YES â€” REFUSE immediately (in the user's language), explain that this violates "
            "honest business principles, and provide a value-driven ethical alternative instead. "
            "Do NOT comply with the unethical request under any circumstances or in any language.\n\n"
            f"{'Business context: ' + business_context + chr(10) + chr(10) if business_context else ''}"
            f"{'Conversation history:' + chr(10) + history_text if history_text else ''}"
            f"User message: {user_message}\n\n"
            "=== YOUR RESPONSE RULES ===\n\n"
            "1. SELF-CONTAINED: Your response must stand completely alone. NEVER write "
            "'strategies listed above', 'as I mentioned', 'see above', 'the following strategies', "
            "'as outlined', or ANY phrase referencing content outside this message. "
            "Write EVERY item, strategy, and recommendation IN FULL in this reply.\n\n"
            "2. DEPTH & SPECIFICITY: Give genuinely expert, specific advice â€” not generic bullet "
            "points. If asked for a marketing strategy, write the FULL strategy with channel "
            "recommendations, messaging approach, target audience analysis, and concrete next "
            "steps. If asked for a tagline, give 5 options with explanations. If asked for brand "
            "colours, give specific hex codes with rationale.\n\n"
            "3. STRUCTURE: Use clear markdown formatting:\n"
            "   - ## for main sections\n"
            "   - **bold** for key terms\n"
            "   - Numbered lists for steps/sequences\n"
            "   - Bullet lists for options/features\n"
            "   - Keep paragraphs short and scannable\n\n"
            "4. VISUALS: If the user requests any visual asset, produce a complete, polished, "
            "self-contained HTML document at the quality level of Pentagram, Wolff Olins, "
            "Landor, or Collins â€” the world's top brand identity studios.\n"
            "   HARD RULES for every visual:\n"
            f"   - {_SVG_BAN}\n"
            f"   - Use Phosphor Icons: {_PHOSPHOR_LINK}\n"
            f"   - {_PHOSPHOR_USAGE_EXAMPLE}\n"
            "   - DYNAMIC PALETTE: invent a unique, industry-specific colour scheme. "
            "     NEVER use emerald or slate. Compute rgba() channels from hex codes directly.\n"
            "   - Google Fonts via @import â€” pick 2 fonts that define the brand personality precisely\n"
            "   - CSS variables in :root {} for ALL colours AND their RGB triplets for rgba() use\n"
            f"   - {_TAILWIND_EXCELLENCE}\n"
           "   - For LOGO: produce a FULL LOGO IDENTITY SYSTEM (not just an icon in a box): "
           "     (1) Symbol mark at 4 sizes (scalability test), "
           "     (2) Wordmark dark-on-light AND light-on-dark, "
           "     (3) Full lockup on dark bg / light bg / brand-colour bg, "
           "     (4) Colour system bar with hex codes and usage labels. "
           "     Symbol = CONSTRUCTED from a signature recipe (Microsoft-style 4-colour "
           "     tile, Google-style per-letter wordmark, Amazon-style smile arc, or layered "
           "     geometric shapes) — NEVER a plain Phosphor icon pasted into a circle, "
           "     NEVER initials in a rounded box. "
           "     Wordmark = precision Google Font + selective accent on 1 letter.\n"
            "   - For SOCIAL POST: do NOT generate any HTML. Deliver a plain-text CONTENT PACK: "
            "     3 post copy variants (Post 1 Hero/Brand Statement, Post 2 Value/Feature, "
            "     Post 3 Community/Story). For each post: headline, body copy (2-4 sentences), "
            "     hashtags, and a detailed photo description the user can search on Unsplash, "
            "     Pexels, or use to brief a photographer (subject, setting, lighting, mood, "
            "     colour tone, search keywords). End with 2-3 platform posting tips. No HTML.\n"
            "   - For BUSINESS CARD: show both front AND back at 700Ã—400px each\n"
            "   - For COLOUR PALETTE: full swatches + hex codes + usage labels + typography preview\n"
            "   - If language is RTL, set <html lang='ar' dir='rtl'> and mirror all layouts\n"
            "   - Wrap the ENTIRE HTML document in ```html\\n...\\n``` fences\n\n"
            + (f"{scaffold_block}\n\n" if scaffold_block else "")
            + "5. TONE: Confident, expert, warm, direct. Sound like a seasoned creative director "
            "who genuinely cares about the client's success.\n\n"
            "Respond now."
        ),
        agent=agent,
        expected_output=(
            "A thorough, expert, fully self-contained response written in the same language "
            "as the user's message (NOT defaulted to English). "
            "If the request was unethical (fake scarcity, FOMO, panic buying), the response "
            "MUST be a polite refusal in the user's language plus a value-driven ethical "
            "alternative â€” no compliance with the unethical request. "
            "Strategic advice must be complete with all content written out in full. "
            "Visual requests must include a ```html ... ``` block at the quality level of "
            "Pentagram / Wolff Olins / Collins: "
            "LOGO requests â†’ full identity system (symbol at 4 sizes + wordmark dark/light + "
            "lockup on 3 backgrounds + colour bar), symbol built from CSS div layers + Phosphor "
            "icon nucleus (not initials in a box), wordmark with accent-letter technique; "
            "SOCIAL POST requests: plain-text content pack only (no HTML) — 3 post copy "
            "variants each with headline, body, hashtags, and photo search description, "
            "plus 2-3 platform posting tips. No HTML artifact for social posts."
        ),
    )


def run_chat(
    user_message: str,
    business_context: str,
    chat_history: list,
) -> str:
    def factory(llm):
        agent = _make_ethical_strategy_director(llm)
        task  = make_chat_task(user_message, business_context, chat_history, agent)
        return task, agent

    return _run_with_fallback(factory, _CHAT_MODELS)

