"""
check_credentials.py
====================
Run this script inside the backend container (or locally with venv active)
to verify IBM Watsonx and Groq credentials before starting the full app.

Usage:
  python check_credentials.py
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

errors = []

# ── IBM Watsonx ──────────────────────────────────────────────────────────────
ibm_api_key    = os.environ.get("IBM_API_KEY", "")
ibm_project_id = os.environ.get("IBM_PROJECT_ID", "")
ibm_url        = os.environ.get("IBM_URL", "https://eu-de.ml.cloud.ibm.com")

print("=" * 60)
print("IBM WATSONX")
print(f"  IBM_URL        : {ibm_url}")
print(f"  IBM_API_KEY    : {'SET (' + ibm_api_key[:6] + '…)' if ibm_api_key else 'MISSING ❌'}")
print(f"  IBM_PROJECT_ID : {'SET (' + ibm_project_id[:8] + '…)' if ibm_project_id else 'MISSING ❌'}")

if not ibm_api_key:
    errors.append("IBM_API_KEY is not set")
if not ibm_project_id:
    errors.append("IBM_PROJECT_ID is not set")

if ibm_api_key and ibm_project_id:
    try:
        from ibm_watsonx_ai import APIClient, Credentials
        creds = Credentials(url=ibm_url, api_key=ibm_api_key)
        client = APIClient(credentials=creds, project_id=ibm_project_id)
        # This call will raise WMLClientError if WML is not associated
        specs = client.foundation_models.get_model_specs()
        model_ids = [m["model_id"] for m in specs.get("resources", [])[:5]]
        print(f"  Connection     : OK ✅  (first 5 models: {model_ids})")
    except Exception as exc:
        print(f"  Connection     : FAILED ❌")
        print(f"  Error          : {exc}")
        errors.append(f"IBM Watsonx connection failed: {exc}")

# ── Groq ─────────────────────────────────────────────────────────────────────
groq_api_key = os.environ.get("GROQ_API_KEY", "")
print()
print("GROQ")
print(f"  GROQ_API_KEY   : {'SET (' + groq_api_key[:6] + '…)' if groq_api_key else 'MISSING ❌'}")

if not groq_api_key:
    errors.append("GROQ_API_KEY is not set")
else:
    try:
        import litellm
        litellm.set_verbose = False
        resp = litellm.completion(
            model="groq/llama-3.1-8b-instant",  # cheap/fast model just for the ping
            messages=[{"role": "user", "content": "Reply with the single word: OK"}],
            api_key=groq_api_key,
            max_tokens=5,
        )
        reply = resp.choices[0].message.content.strip()
        print(f"  Connection     : OK ✅  (response: '{reply}')")
    except Exception as exc:
        print(f"  Connection     : FAILED ❌")
        print(f"  Error          : {exc}")
        errors.append(f"Groq connection failed: {exc}")

# ── Summary ──────────────────────────────────────────────────────────────────
print()
print("=" * 60)
if errors:
    print(f"RESULT: {len(errors)} issue(s) found ❌")
    for e in errors:
        print(f"  • {e}")
    sys.exit(1)
else:
    print("RESULT: All credentials OK ✅")
    sys.exit(0)
