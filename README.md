# Ethical Brand Studio
**AI-Powered Ethical & Modest Brand Strategy Platform**  
*Built for the IBM AI Builders Challenge — "Reimagine Creative Industries with AI"*

---

## Problem Statement

Entrepreneurs in the Muslim-majority world (MENA, Southeast Asia, Sub-Saharan Africa) — a market of 1.8 billion people — have no AI branding tool built for their values. Mainstream AI generators produce landing pages filled with alcohol references, imagery of people/animals forbidden in Islamic branding, or manipulative "FOMO" marketing tactics. These businesses are completely underserved.

**Ethical Brand Studio solves this directly:** it is the world's first AI brand platform where ethics and compliance are baked into the model pipeline, not bolted on as a filter.

---

## Solution Description

Ethical Brand Studio is a full-stack AI web application that lets any entrepreneur — regardless of design or copywriting skill — instantly generate:

- **A production-ready branded landing page** (complete HTML, styled with Tailwind CSS, unique industry-specific colour palette, RTL-aware for Arabic/Hebrew/Farsi)
- **An AI Brand Growth Assistant** chat that delivers brand strategy, content ideas, colour palettes, logo concepts, and visual mockups — all in the user's own language

The platform supports 10+ languages with automatic detection, full RTL layout for Arabic and Hebrew, and hard ethical guardrails that refuse fake scarcity, FOMO tactics, and deceptive marketing.

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
        │  4th  openrouter/qwen3-coder-480b-a35b  (free, optional) │
        │  5th  huggingface/Llama-3.3-70B-Instruct (free, optional)│
        │  6th  groq/llama-3.1-8b-instant         (small-pool net) │
        │  7th  openai/gpt-4o-mini               (no daily cap)    │
        └──────────────────────────────────────────────────────────┘
```

### Agent 1 — PlatformEngineer
Generates complete, pixel-perfect, single-file HTML landing pages.  
- Tailwind CSS + Phosphor Icons + Google Fonts, zero raw SVG
- Industry-specific dynamic colour palettes (never repeats a scheme)
- Automatic RTL layout for Arabic, Hebrew, Farsi, Urdu
- Gold-standard design-system scaffold injected into every task — a token-budgeted
  professional brief covering head assets, industry palette table, 7-section flow,
  custom CSS classes, and RTL rules
- Pydantic output validator salvages accidental markdown wrapping
- Because every Groq model has its own daily token pool, each tier in the ladder is
  independent — running out of one model doesn't take down the next

### Agent 2 — EthicalStrategyDirector
Elite brand strategist, creative director, and ethics guardian — operating at the level of **Pentagram, Wolff Olins, Landor, and Collins**.

**Logo Identity System** — not just an icon in a box. Every logo request produces a complete 5-section identity sheet:
1. Symbol mark isolated at 4 sizes (64px → 18px favicon scalability test)
2. Wordmark alone — dark-on-light and light-on-dark
3. Full lockup (symbol + wordmark) on dark background, light background, and brand-colour background
4. Colour system bar with hex codes and usage labels
5. Typography pairing preview

The symbol is built from **layered CSS `div` shapes** (`border-radius`, `clip-path`, `transform:rotate`) with a Phosphor icon as the semantic nucleus — inspired by how Google, Microsoft, Nike, and Apple approach mark construction.

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
| 1 — Input | `validate_business_input()` | Blocks haram categories before any LLM call |
| 2 — Output | `validate_agent_output()` | Scans every LLM output for leaked haram content |
| 3 — Agent | `COMPLIANCE_SYSTEM` prompt | LLM-as-gatekeeper semantic final check |

### Language Detection (`main.py`)
Unicode-block heuristics detect Arabic, Hebrew, Chinese, Japanese, Korean, Hindi, Thai, French, and Spanish automatically — no external library dependency. Output language and layout direction match the detected input language.

---

## Selected Challenge Theme

**Reimagine Creative Industries with AI**

Branding and creative direction have historically been gated behind expensive agencies or tools that ignore ethical and cultural constraints. Ethical Brand Studio democratises professional brand creation for entrepreneurs in underserved communities — specifically the 1.8 billion Muslims worldwide — using AI to make culturally-aware, ethics-first creative output accessible to anyone with a business idea.

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
| LLM — Fallback | **OpenRouter** (free qwen3-coder-480b) → **Hugging Face** (free Llama-3.3-70B) → **OpenAI** (gpt-4o-mini) |
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
| **Generate Landing Page** | Type a business description (any language) → click **Generate Site** |
| **AI Strategy Chat** | Ask any brand/marketing question in the right panel |
| **Logo Identity System** | Ask for a "logo" → get a full symbol + wordmark + lockup system at 3 backgrounds + scalability test |
| **Social Content Pack** | Ask for a "social post" → get 3 copy-ready post variants (Hero, Value, Story) with headlines, body copy, hashtags, and photo search suggestions for each |
| **Colour Palette** | Ask for a "colour palette" → get full swatches + hex codes + usage labels + typography preview |
| **RTL Layout** | Write your prompt in Arabic, Hebrew, or Farsi — the generated page mirrors to RTL |
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
| `OPENROUTER_API_KEY` | Optional | OpenRouter key — adds free qwen3-coder-480b to the ladder; leave empty to skip |
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
  "user_message": "Design a logo concept for my brand",
  "business_context": "Organic honey store in Cairo",
  "chat_history": []
}

// Response
{
  "text": "Here is a logo concept for your brand:",
  "artifact_html": "<!DOCTYPE html>..."
}
```

### `GET /health`
Returns `{"status": "ok"}` — used by Docker health checks.

---

## Ethical Design Principles

This platform is built around **Maqasid al-Shariah** (the higher objectives of Islamic law) as applied to business:

1. **No deception (Gharar)** — AI refuses to generate fake scarcity, false stock alerts, or manipulative FOMO copy
2. **No harm (Darar)** — All haram business categories are blocked at input before any LLM call
3. **Honest value creation** — Strategy recommendations focus on genuine quality and authentic customer relationships
4. **Community first** — Growth strategies prioritise organic community building over aggressive paid acquisition

---

## License

MIT License — see [LICENSE](LICENSE) for details.
