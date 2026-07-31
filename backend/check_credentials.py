"""
check_credentials.py
====================
Run this script inside the backend container (or locally with venv active)
to verify all configured LLM provider credentials before starting the full app.

Providers: Groq (primary), OpenAI (final fallback), plus optional
OpenRouter and HuggingFace free-tier fallbacks.

Usage:
  python check_credentials.py
"""

import os
import sys

from dotenv import load_dotenv

# Windows consoles default to cp1252 and crash on the emoji below — force UTF-8.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

load_dotenv()

errors = []


def probe(provider: str, model: str, api_key: str, note: str = "") -> None:
    print(f"  Connection     : ", end="")
    try:
        import litellm
        litellm.set_verbose = False
        resp = litellm.completion(
            model=model,
            messages=[{"role": "user", "content": "Reply with the single word: OK"}],
            api_key=api_key,
            max_tokens=5,
        )
        reply = resp.choices[0].message.content.strip()
        print(f"OK ✅  (response: '{reply}')")
    except Exception as exc:
        print("FAILED ❌")
        print(f"  Error          : {exc}")
        errors.append(f"{provider} connection failed: {exc}")


# ── Groq (primary) ────────────────────────────────────────────────────────────
groq_api_key = os.environ.get("GROQ_API_KEY", "")

print("=" * 60)
print("GROQ  (primary provider)")
print(f"  GROQ_API_KEY   : {'SET (' + groq_api_key[:6] + '…)' if groq_api_key else 'MISSING ❌'}")

if not groq_api_key:
    errors.append("GROQ_API_KEY is not set")
else:
    probe("Groq", "groq/llama-3.1-8b-instant", groq_api_key, "cheap/fast ping model")
    probe("Groq", "groq/openai/gpt-oss-120b", groq_api_key, "ladder model")
    probe("Groq", "groq/qwen/qwen3.6-27b", groq_api_key, "ladder model")

# ── OpenAI (final fallback) ───────────────────────────────────────────────────
openai_api_key = os.environ.get("OPENAI_API_KEY", "")
print()
print("OPENAI  (final fallback)")
print(f"  OPENAI_API_KEY : {'SET (' + openai_api_key[:6] + '…)' if openai_api_key else 'MISSING (optional if Groq healthy)'}")

if openai_api_key:
    probe("OpenAI", "openai/gpt-4o-mini", openai_api_key)

# ── OpenRouter (optional free fallback) ───────────────────────────────────────
openrouter_api_key = os.environ.get("OPENROUTER_API_KEY", "")
print()
print("OPENROUTER  (optional free fallback)")
print(f"  OPENROUTER_API_KEY : {'SET (' + openrouter_api_key[:6] + '…)' if openrouter_api_key else 'EMPTY (provider skipped)'}")

if openrouter_api_key:
    probe("OpenRouter", "openrouter/google/gemma-4-26b-a4b-it:free", openrouter_api_key)
    probe("OpenRouter", "openrouter/poolside/laguna-s-2.1:free", openrouter_api_key)

# ── HuggingFace (optional free fallback) ──────────────────────────────────────
hf_api_key = os.environ.get("HF_API_KEY", "")
print()
print("HUGGING FACE  (optional free fallback)")
print(f"  HF_API_KEY         : {'SET (' + hf_api_key[:6] + '…)' if hf_api_key else 'EMPTY (provider skipped)'}")

if hf_api_key:
    probe("HuggingFace", "huggingface/meta-llama/Llama-3.3-70B-Instruct", hf_api_key)

# ── Summary ──────────────────────────────────────────────────────────────────
print()
print("=" * 60)
if errors:
    print(f"RESULT: {len(errors)} issue(s) found ❌")
    for e in errors:
        print(f"  • {e}")
    sys.exit(1)
else:
    print("RESULT: All configured credentials OK ✅")
    sys.exit(0)
