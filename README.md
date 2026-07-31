# Ethical Brand Studio
**AI-Powered Ethical Brand Strategy Platform**  
*Built for the IBM AI Builders Challenge — "Reimagine Creative Industries with AI"*

---

## Problem Statement

Entrepreneurs worldwide — especially in underserved emerging markets (MENA, Southeast Asia, Sub-Saharan Africa) — have no AI branding tool built around their values and ethical standards. Mainstream AI generators produce landing pages filled with manipulative "FOMO" marketing tactics, deceptive scarcity claims, and culturally inappropriate imagery. These businesses are completely underserved.

**Ethical Brand Studio solves this directly:** it is the world's first AI brand platform where ethics and compliance are baked into the model pipeline, not bolted on as a filter.

---

## Solution Description

Ethical Brand Studio is a full-stack AI web application that lets any entrepreneur — regardless of design or copywriting skill — instantly generate:

- **A production-ready branded landing page** (complete HTML in an IBM BöC-style design language — IBM Plex typography, Carbon palette, flat rectangular geometry, hairline borders; RTL-aware for Arabic/Farsi)
- **An AI Brand Growth Assistant** chat that delivers brand strategy, logo concept directions, content ideas, colour palettes, and visual mockups — all in the user's own language

The platform supports 10+ languages with automatic detection, full RTL layout for Arabic, and hard ethical guardrails that refuse fake scarcity, FOMO tactics, and deceptive marketing.

---

## AI Approach & Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    FRONTEND  (Next.js 14)                        │
│                                                                  │
│  app/page.tsx         Split-screen canvas + brand form          │
│  components/          BrandAssistant · ArtifactRenderer         │
│                        StrategyChat · LivePreview                │
└──────────────────────────┬───────────────────────────────────────┘
                           │  HTTP (reverse-proxied via /api/backend)
┌──────────────────────────▼───────────────────────────────────────┐
│                    BACKEND  (FastAPI + CrewAI)                   │
│                                                                  │
│  main.py              /api/generate-site · /api/chat            │
│  crew.py              Two-agent CrewAI pipeline                  │
│                         • Agent 1: PlatformEngineer             │
│                         • Agent 2: EthicalStrategyDirector      │
│  guardrails.py        Three-layer ethical compliance system     │
│  image_gen.py         AI visual generation (HTML artifacts)     │
│  exporter.py          ZIP download of generated assets          │
└──────────────────────────────────────────────────────────────────┘

                     MODEL FALLBACK LADDER
        ┌──────────────────────────────────────────────────────────┐
        │  1st  groq/llama-3.3-70b-versatile       (12k TPM pool)  │
        │  2nd  groq/openai/gpt-oss-120b           (separate pool) │
        │  3rd  groq/qwen/qwen3.6-27b              (separate pool) │
        │  4th  openrouter/gemma-4-26b          (free, optional)   │
        │  5th  openrouter/poolside/laguna-s-2.1 (free, optional)  │
        │  6th  huggingface/Llama-3.3-70B-Instruct(free, optional) │
        │  7th  groq/llama-3.1-8b-instant         (small-pool net) │
        │  8th  openai/gpt-4o-mini               (no daily cap)    │
        └──────────────────────────────────────────────────────────┘
```

### Agent 1 — PlatformEngineer
Generates complete, pixel-perfect, single-file HTML landing pages in an **IBM BöC (B/OLD) design language**:  
- IBM Plex Sans/Mono typography, Carbon colour system, flat rectangular geometry, hairline borders, generous whitespace — no glow, no glass, no 3D
- Tailwind CSS + Phosphor Icons + Google Fonts, zero raw SVG
- Industry-specific dynamic colour palettes (never repeats a scheme)
- Automatic RTL layout for Arabic, Farsi, Urdu
- Gold-standard design-system scaffold injected into every task — a token-budgeted
  professional brief covering head assets, Carbon palette table, 7-section flow,
  custom CSS classes, and RTL rules
- Completeness validation + Pydantic output validator: a page is only returned when
  it is a closed, styled document with all interaction rules (safe `#hash` anchors,
  `mailto:` CTAs, `<button type="button">`) — truncated or broken pages are rejected
  and the next model in the ladder is tried
- Because every Groq model has its own daily token pool, each tier in the ladder is
  independent — running out of one model doesn't take down the next

### Agent 2 — EthicalStrategyDirector
Elite brand strategist, creative director, and ethics guardian — operating at the level of **Pentagram, Wolff Olins, Landor, and Collins**.

**Logo Concept Directions (text-only)** — rendered logo visuals are no longer produced. Every logo request is answered with a pure-text concept brief:
1. **Three distinct logo concepts**, each with a name, the symbol idea in one vivid sentence, and the one-line meaning behind it
2. A **brand strategy** — positioning, target audience, tone, and colour direction — built around those concepts
3. The Focus Group Simulator (below) to close

The idea is the deliverable — a complete brief the entrepreneur can hand to any designer, without a blank or broken AI-rendered visual.

**AI Focus Group Simulator** — every strategy response ends with a **Target Audience Simulation** section (محاكاة ردود أفعال الجمهور) that roleplays **3 distinct potential customers** (e.g. a skeptical university student, a busy parent, a local shop owner). For each persona it writes a profile, a verbatim quote reacting to the brand idea, their top concern, what would convert them, and a buy/not-buy verdict — then closes with a synthesis of the single shared objection and the change that neutralises it.

**Social Media Content Pack** — no low-quality generated images. Every social request produces a **ready-to-use text content pack**:
1. **Post 1 — Hero/Brand Statement**: punchy headline, bold body copy, hashtags + photo search terms
2. **Post 2 — Value/Feature**: educational copy highlighting a key benefit, hashtags + photo search terms
3. **Post 3 — Community/Story**: warm, authentic community message, hashtags + photo search terms
4. **Platform tips**: 2–3 posting tips tailored to the brand's industry and audience

The user receives complete, copy-paste-ready post text plus specific photo descriptions they can search on Unsplash, Pexels, or use to brief a photographer — no generated imagery with quality limitations.

- Hard refusal of fake scarcity, FOMO, deceptive copy (zero tolerance)
- Responds entirely in the user's detected language
- Three-layer guardrails: input validation → LLM output scan → agent-level semantic check

### Three-Layer Ethical Guardrails (`guardrails.py`)
| Layer | Function | What it checks |
|---|---|---|
| 1 — Input | `validate_business_input()` | Blocks ethically problematic business categories before any LLM call |
| 2 — Output | `validate_agent_output()` | Scans every LLM output for leaked restricted content |
| 3 — Agent | `COMPLIANCE_SYSTEM` prompt | LLM-as-gatekeeper semantic final check |

### Language Detection (`main.py`)
Unicode-block heuristics detect Arabic, Chinese, Japanese, Korean, Hindi, Thai, French, and Spanish automatically — no external library dependency. Output language and layout direction match the detected input language.

---

## Selected Challenge Theme

**Reimagine Creative Industries with AI**

Branding and creative direction have historically been gated behind expensive agencies or tools that ignore ethical and cultural constraints. Ethical Brand Studio democratises professional brand creation for entrepreneurs in underserved communities and values-driven businesses worldwide — using AI to make culturally-aware, ethics-first creative output accessible to anyone with a business idea.

---

## How IBM Bob Was Used

IBM Bob (the AI assistant) was used as the **primary development tool** throughout this project:

- **Architecture design** — Bob guided the CrewAI two-agent pipeline design and the model fallback ladder strategy
- **Code generation & refinement** — The full-stack codebase (FastAPI backend, Next.js frontend, Docker setup) was built iteratively with Bob
- **Guardrails system** — Bob helped design and implement the three-layer ethical compliance system in [`guardrails.py`](backend/guardrails.py)
- **Prompt engineering** — The gold-standard HTML scaffold and agent backstory prompts in [`crew.py`](backend/crew.py) were crafted with Bob's assistance
- **Debugging** — LiteLLM `cache_breakpoint` Groq compatibility issue was diagnosed and resolved with Bob
- **Submission preparation** — This README and the final submission checklist were completed with Bob

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 · React 18 · Tailwind CSS 3 · TypeScript |
| Backend | FastAPI · Uvicorn · Python 3.11 |
| AI Orchestration | CrewAI (multi-agent pipeline) |
| LLM — Primary | Groq (llama-3.3-70b-versatile, gpt-oss-120b, qwen3.6-27b, llama-3.1-8b-instant) |
| LLM — Fallback | **OpenRouter** (free gemma-4-26b, poolside laguna-s-2.1) → **Hugging Face** (free Llama-3.3-70B) → **OpenAI** (gpt-4o-mini) |
| Artifact Rendering | Sandboxed `<iframe srcDoc>` — zero XSS risk |
| Containerisation | Docker + Docker Compose |
| Deployment | Render (backend) · Vercel (frontend) |
| Ethical Layer | Custom 3-layer guardrail system (input + output + LLM-agent) |

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- A [Groq API key](https://console.groq.com) (free)
- *(Optional)* An [OpenAI API key](https://platform.openai.com/api-keys) for the final fallback
- *(Optional)* An [OpenRouter key](https://openrouter.ai/keys) and/or [Hugging Face token](https://huggingface.co/settings/tokens) for extra free-tier fallback capacity

### 1. Clone & configure

```bash
git clone https://github.com/<your-username>/branding-ai.git
cd branding-ai
```

### 2. Backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Edit .env — add your GROQ_API_KEY (and OPENAI_API_KEY for the final fallback;
# OPENROUTER_API_KEY / HF_API_KEY are optional free-tier fallbacks)

python check_credentials.py  # optional — verifies every configured provider

uvicorn main:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
# Opens on http://localhost:3000
```

### 4. Docker (full stack)

```bash
# From the project root
cp backend/.env.example backend/.env
# Edit backend/.env and add your API keys

docker compose up --build
# Frontend → http://localhost:3000
# Backend  → http://localhost:8000
```

---

## Features

| Feature | How |
|---|---|
| **Generate Landing Page** | Type a business description (any language) → click **Generate Site** — an IBM BöC-style premium page with safe navigation |
| **AI Strategy Chat** | Ask any brand/marketing question in the right panel |
| **AI Focus Group Simulator** | Every strategy ends with a Target Audience Simulation roleplaying 3 distinct customers (profile, quote, concern, what converts them, verdict) + a synthesis |
| **Logo Concept Directions** | Ask for a "logo" → get a text-only brief of 3 logo concepts (name + symbol idea + meaning) plus brand strategy — no blank visuals |
| **Social Content Pack** | Ask for a "social post" → get 3 copy-ready post variants (Hero, Value, Story) with headlines, body copy, hashtags, and photo search suggestions for each |
| **Colour Palette** | Ask for a "colour palette" → get full swatches + hex codes + usage labels + typography preview |
| **RTL Layout** | Write your prompt in Arabic or Farsi — the generated page mirrors to RTL |
| **Ethical Guardrails** | The platform auto-refuses fake scarcity, FOMO, and deceptive marketing requests |
| **Download** | Click **Download** on any artifact card to save the HTML |

---

## Project Structure

```
branding-ai/
├── backend/
│   ├── main.py            # FastAPI app, language detection, artifact extraction
│   ├── crew.py            # CrewAI agents, model fallback ladder, prompts
│   ├── guardrails.py      # 3-layer ethical compliance system
│   ├── image_gen.py       # Visual artifact generation helpers
│   ├── exporter.py        # ZIP asset download
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── app/
│   │   ├── page.tsx           # Main split-screen UI
│   │   └── api/backend/       # Next.js reverse proxy to FastAPI
│   ├── components/
│   │   ├── BrandAssistant.tsx # AI chat panel
│   │   ├── ArtifactRenderer.tsx
│   │   ├── LivePreview.tsx
│   │   └── StrategyChat.tsx
│   ├── Dockerfile
│   └── .env.local.example
├── docker-compose.yml
└── README.md
```

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | Yes | Groq API key — primary LLM provider |
| `OPENAI_API_KEY` | Optional | OpenAI API key — final fallback (gpt-4o-mini), no daily cap |
| `OPENROUTER_API_KEY` | Optional | OpenRouter key — adds free gemma-4-26b and poolside laguna-s-2.1 to the ladder; leave empty to skip |
| `HF_API_KEY` | Optional | Hugging Face token — adds free Llama-3.3-70B-Instruct to the ladder; leave empty to skip |

### Frontend (`frontend/.env.local`)

| Variable | Description |
|---|---|
| `BACKEND_URL` | URL of the FastAPI backend (default: `http://localhost:8000`) |
| `NEXT_PUBLIC_BACKEND_URL` | Same URL, exposed to the browser |

---

## API Reference

### `POST /api/generate-site`
Generates a complete HTML landing page.

```json
// Request
{ "business_description": "Organic honey store in Cairo" }

// Response
{ "html": "<!DOCTYPE html>..." }
```

### `POST /api/chat`
AI strategy chat with optional artifact generation.

```json
// Request
{
  "user_message": "Give me a full marketing strategy for my brand",
  "business_context": "Organic honey store in Cairo",
  "chat_history": []
}

// Response
{
  "text": "...strategy ending with a Target Audience Simulation...",
  "artifact_html": null
}
```

Logo requests return text-only concept directions (no `artifact_html`). Requests for colour palettes, business cards, or other HTML artifacts populate `artifact_html`.

### `GET /health`
Returns `{"status": "ok"}` — used by Docker health checks.

---

## Ethical Design Principles

This platform is built around universal principles of honest business that respect every culture and faith:

1. **No deception** — AI refuses to generate fake scarcity, false stock alerts, or manipulative FOMO copy
2. **No harm** — ethically problematic business categories are blocked at input before any LLM call
3. **Honest value creation** — Strategy recommendations focus on genuine quality and authentic customer relationships
4. **Community first** — Growth strategies prioritise organic community building over aggressive paid acquisition

---

## License

MIT License — see [LICENSE](LICENSE) for details.
