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
    Groq models are tried first in priority order (separate daily token pools).
    IBM Watsonx is the final safety net â€” enterprise-grade, no daily token cap.
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

_TAILWIND_EXCELLENCE = (
    "=== ELITE UI/UX â€” TAILWIND CSS ===\n"
    "- Use glassmorphism where appropriate: bg-white/10 backdrop-blur-md border border-white/20\n"
    "- Rich gradient backgrounds using the BRAND PALETTE hex codes â€” never Tailwind defaults\n"
    "- Soft depth: shadow-xl shadow-black/20 ring-1 ring-white/10\n"
    "- Generous spacing (py-20 â†’ py-32 between sections) with rounded-2xl / rounded-3xl cards\n"
    "- Hover micro-interactions: hover:-translate-y-1 transition-transform duration-300\n"
    "- Responsive: mobile-first, sm: md: lg: breakpoints used throughout\n\n"
    "=== DYNAMIC COLOUR SYSTEM â€” MANDATORY ===\n"
    "âš ï¸  NEVER use the same colour scheme twice. NEVER default to emerald/slate/green or any "
    "previously used palette. You MUST invent a UNIQUE palette each time, driven entirely by "
    "the user's specific brand industry, mood, and cultural context.\n\n"
    "PALETTE SELECTION GUIDE â€” detect the industry and commit to ONE palette fully:\n"
    "â€¢ Luxury / Jewellery / Premium Fashion â†’\n"
    "  deep midnight navy #0a0a1a + rich gold #c9a84c + ivory #f5f0e8 + warm white text\n"
    "â€¢ Health / Wellness / Organic / Natural â†’\n"
    "  deep forest green #1a3a2a + sage #7aab8a + warm sand #f2ebe0 + terracotta accent #c4714a\n"
    "â€¢ Tech / SaaS / Digital â†’\n"
    "  deep space black #070714 + electric indigo #5c4df5 + neon cyan #00e5ff + light lavender text\n"
    "â€¢ Food / CafÃ© / Restaurant â†’\n"
    "  warm espresso #1c1008 + burnt orange #e8602c + cream #fdf6ec + golden yellow #f0b429\n"
    "â€¢ Beauty / Cosmetics / Skincare â†’\n"
    "  blush rose #fce8e8 + dusty mauve #b07080 + deep plum #3d1a2a + champagne gold #d4af7a\n"
    "â€¢ Sport / Fitness / Active â†’\n"
    "  carbon black #0f0f0f + electric lime #b0f030 + steel grey #3a3a4a + vivid red #e63030\n"
    "â€¢ Real Estate / Architecture â†’\n"
    "  slate #1a1f2e + warm bronze #8a6a42 + off-white #f4f1ec + graphite #3a3a3a\n"
    "â€¢ Education / Learning / Academy â†’\n"
    "  deep teal #0d3349 + golden amber #e8a820 + pure white #ffffff + sky blue #4db8e8\n"
    "â€¢ Finance / Legal / Consulting â†’\n"
    "  dark charcoal #151520 + deep royal blue #1a3a8f + silver #c0c8d8 + gold #c9a44a\n"
    "â€¢ Kids / Toys / Family â†’\n"
    "  soft navy #1a2a5e + sunny yellow #f5c518 + coral red #e84444 + sky blue #5ab4e8\n"
    "â€¢ Medical / Clinic / Pharmacy â†’\n"
    "  deep navy #0a1628 + clinical cyan #00b8d9 + slate grey #475569 + pure white #ffffff\n"
    "â€¢ Artisan / Handcraft / Heritage â†’\n"
    "  warm leather #3b1f0e + sienna #a0522d + parchment #f8f0e3 + olive green #5a6e2e\n\n"
    "COLOUR RULES (non-negotiable):\n"
    "1. Hero section: must use the darkest base as full-bleed background with a rich gradient overlay\n"
    "2. Primary CTA button: the most vivid accent colour with a glow box-shadow matching that colour\n"
    "3. Cards/features: glassmorphism using the primary colour at 8â€“15% opacity as background\n"
    "4. Section alternation: alternate between the dark base and a slightly lighter surface tone\n"
    "5. Typography: headings in the lightest/warmest tone, body in muted mid-tone, captions faded\n"
    "6. NEVER use default Tailwind colours (blue-500, gray-700, emerald-*, etc.) â€” "
    "   always use the custom palette hex codes registered in tailwind.config\n"
    "7. The nav must use glassmorphism blur with the base colour at 85% opacity"
)


# â”€â”€ Gold-standard HTML scaffold (few-shot reference) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# This is injected into the PlatformEngineer's task description as a concrete
# structural reference. LLMs are few-shot learners â€” seeing a complete, correctly
# structured example produces dramatically better output than rules alone.
# The scaffold uses PLACEHOLDER values that the agent must replace with real
# brand-specific content and a brand-appropriate colour palette.

_GOLD_SCAFFOLD = """
=== GOLD-STANDARD STRUCTURAL REFERENCE ===
Study this scaffold carefully. You MUST produce output at EXACTLY this level of
structure, completeness, and polish â€” but with real brand content, the correct
language, and a unique industry-appropriate colour palette instead of the
placeholder values shown here.

```html
<!DOCTYPE html>
<html lang="DETECTED_LANG" dir="DETECTED_DIR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>BRAND NAME â€” Tagline</title>

  <!-- Tailwind CSS CDN -->
  <script src="https://cdn.tailwindcss.com"></script>

  <!-- Phosphor Icons CDN â€” ALL icons must come from here -->
  <link rel="stylesheet" type="text/css"
        href="https://unpkg.com/@phosphor-icons/web@2.1.1/src/regular/style.css" />

  <!-- Google Fonts -->
  <style>
    @import url('https://fonts.googleapis.com/css2?family=DISPLAY_FONT:wght@400;700;800&family=BODY_FONT:wght@300;400;500&display=swap');

    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    html { scroll-behavior: smooth; }
    body { font-family: 'BODY_FONT', sans-serif; background: var(--base); color: var(--text-light); overflow-x: hidden; }
    .font-display { font-family: 'DISPLAY_FONT', sans-serif; }

    :root {
      --base:        #DARKEST_HEX;
      --surface:     #SLIGHTLY_LIGHTER_HEX;
      --card:        #CARD_BG_HEX;
      --primary:     #PRIMARY_ACCENT_HEX;
      --secondary:   #SECONDARY_ACCENT_HEX;
      --text-light:  #LIGHTEST_TEXT_HEX;
      --text-muted:  #MUTED_TEXT_HEX;
    }

    /* Gradient text */
    .g-text {
      background: linear-gradient(135deg, var(--text-light) 0%, var(--primary) 50%, var(--secondary) 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }

    /* Glassmorphism card */
    .card {
      background: rgba(PRIMARY_RGB, 0.08);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border: 1px solid rgba(PRIMARY_RGB, 0.15);
      border-radius: 20px;
      padding: 32px 28px;
      transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
    }
    .card:hover {
      transform: translateY(-4px);
      border-color: rgba(PRIMARY_RGB, 0.4);
      box-shadow: 0 16px 48px rgba(PRIMARY_RGB, 0.15);
    }

    /* CTA button */
    .btn-primary {
      display: inline-flex; align-items: center; gap: 10px;
      padding: 16px 36px; border-radius: 50px;
      background: var(--primary);
      color: var(--text-light);
      font-family: 'DISPLAY_FONT', sans-serif;
      font-size: 1rem; font-weight: 700; letter-spacing: 0.02em;
      border: none; cursor: pointer;
      box-shadow: 0 0 32px rgba(PRIMARY_RGB, 0.45), 0 8px 24px rgba(0,0,0,0.3);
      transition: transform 0.2s ease, box-shadow 0.2s ease;
      text-decoration: none;
    }
    .btn-primary:hover {
      transform: translateY(-2px);
      box-shadow: 0 0 48px rgba(PRIMARY_RGB, 0.6), 0 12px 32px rgba(0,0,0,0.4);
    }

    /* Sticky nav */
    nav {
      position: sticky; top: 0; z-index: 50;
      background: rgba(DARKEST_RGB, 0.88);
      backdrop-filter: blur(18px) saturate(1.5);
      -webkit-backdrop-filter: blur(18px) saturate(1.5);
      border-bottom: 1px solid rgba(PRIMARY_RGB, 0.12);
    }

    /* Section alternation helpers */
    .section-dark    { background: var(--base); }
    .section-surface { background: var(--surface); }
  </style>

  <!-- Tailwind custom palette registration -->
  <script>
    tailwind.config = {
      theme: {
        extend: {
          colors: {
            base:      'var(--base)',
            surface:   'var(--surface)',
            card:      'var(--card)',
            primary:   'var(--primary)',
            secondary: 'var(--secondary)',
          },
          fontFamily: {
            display: ['DISPLAY_FONT', 'sans-serif'],
            body:    ['BODY_FONT',    'sans-serif'],
          }
        }
      }
    }
  </script>
</head>
<body>

<!-- â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• STICKY NAV â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• -->
<nav>
  <div style="max-width:1100px;margin:0 auto;padding:14px 32px;display:flex;align-items:center;justify-content:space-between;">
    <!-- Logo mark: Phosphor icon + brand name -->
    <a href="#hero" style="display:flex;align-items:center;gap:12px;text-decoration:none;">
      <div style="width:40px;height:40px;border-radius:12px;background:var(--primary);display:flex;align-items:center;justify-content:center;box-shadow:0 0 20px rgba(PRIMARY_RGB,0.4);">
        <i class="ph ph-RELEVANT_ICON" style="font-size:20px;color:var(--text-light);"></i>
      </div>
      <div>
        <div style="font-family:'DISPLAY_FONT',sans-serif;font-size:16px;font-weight:800;color:var(--text-light);letter-spacing:0.01em;line-height:1.1;">BRAND NAME</div>
        <div style="font-size:10px;color:var(--text-muted);letter-spacing:0.07em;text-transform:uppercase;">BRAND TAGLINE SHORT</div>
      </div>
    </a>
    <!-- Nav links -->
    <div style="display:flex;gap:28px;align-items:center;">
      <a href="#about"    style="font-size:14px;color:var(--text-muted);text-decoration:none;transition:color .2s;" onmouseover="this.style.color='var(--text-light)'" onmouseout="this.style.color='var(--text-muted)'">ABOUT_LABEL</a>
      <a href="#features" style="font-size:14px;color:var(--text-muted);text-decoration:none;transition:color .2s;" onmouseover="this.style.color='var(--text-light)'" onmouseout="this.style.color='var(--text-muted)'">FEATURES_LABEL</a>
      <a href="#contact"  style="font-size:14px;color:var(--text-muted);text-decoration:none;transition:color .2s;" onmouseover="this.style.color='var(--text-light)'" onmouseout="this.style.color='var(--text-muted)'">CONTACT_LABEL</a>
      <a href="#contact" class="btn-primary" style="padding:10px 22px;font-size:13px;">CTA_LABEL <i class="ph ph-arrow-right"></i></a>
    </div>
  </div>
</nav>

<!-- â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• HERO â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• -->
<section id="hero" class="section-dark" style="position:relative;overflow:hidden;padding:120px 32px 100px;text-align:center;">
  <!-- Radial glow background element using CSS only, no SVG -->
  <div style="position:absolute;inset:0;pointer-events:none;background:radial-gradient(ellipse 80% 60% at 50% 40%, rgba(PRIMARY_RGB,0.18) 0%, transparent 65%);"></div>

  <div style="max-width:760px;margin:0 auto;position:relative;z-index:1;">
    <!-- Eyebrow label -->
    <div style="display:inline-flex;align-items:center;gap:8px;padding:6px 18px;border-radius:999px;background:rgba(PRIMARY_RGB,0.1);border:1px solid rgba(PRIMARY_RGB,0.25);margin-bottom:32px;">
      <i class="ph ph-EYEBROW_ICON" style="font-size:13px;color:var(--primary);"></i>
      <span style="font-size:12px;font-weight:600;color:var(--primary);letter-spacing:0.08em;text-transform:uppercase;">EYEBROW_LABEL</span>
    </div>

    <!-- Main headline -->
    <h1 class="font-display g-text" style="font-size:clamp(2.8rem,6vw,4.5rem);font-weight:800;line-height:1.05;letter-spacing:-0.02em;margin-bottom:24px;">
      COMPELLING HEADLINE<br/>SECOND LINE OF HEADLINE
    </h1>

    <!-- Subheadline -->
    <p style="font-size:1.1rem;line-height:1.85;color:var(--text-muted);max-width:560px;margin:0 auto 48px;">
      SUBHEADLINE describing the brand's core value proposition in 2â€“3 sentences.
      Speak directly to the target audience's needs and aspirations.
    </p>

    <!-- CTA button -->
    <a href="#contact" class="btn-primary">
      <i class="ph ph-HERO_CTA_ICON" style="font-size:18px;"></i>
      HERO_CTA_TEXT
    </a>
  </div>
</section>

<!-- â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• TRUST BAR â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• -->
<section class="section-surface" style="padding:40px 32px;border-top:1px solid rgba(PRIMARY_RGB,0.1);border-bottom:1px solid rgba(PRIMARY_RGB,0.1);">
  <div style="max-width:900px;margin:0 auto;display:flex;flex-wrap:wrap;justify-content:center;gap:40px;">
    <!-- Trust item 1 â€” drawn from real business description -->
    <div style="display:flex;align-items:center;gap:12px;">
      <i class="ph ph-TRUST_ICON_1" style="font-size:24px;color:var(--primary);"></i>
      <div>
        <div style="font-family:'DISPLAY_FONT',sans-serif;font-size:1.4rem;font-weight:800;color:var(--text-light);">TRUST_STAT_1</div>
        <div style="font-size:12px;color:var(--text-muted);letter-spacing:0.04em;">TRUST_LABEL_1</div>
      </div>
    </div>
    <!-- Trust item 2 -->
    <div style="display:flex;align-items:center;gap:12px;">
      <i class="ph ph-TRUST_ICON_2" style="font-size:24px;color:var(--secondary);"></i>
      <div>
        <div style="font-family:'DISPLAY_FONT',sans-serif;font-size:1.4rem;font-weight:800;color:var(--text-light);">TRUST_STAT_2</div>
        <div style="font-size:12px;color:var(--text-muted);letter-spacing:0.04em;">TRUST_LABEL_2</div>
      </div>
    </div>
    <!-- Trust item 3 -->
    <div style="display:flex;align-items:center;gap:12px;">
      <i class="ph ph-TRUST_ICON_3" style="font-size:24px;color:var(--primary);"></i>
      <div>
        <div style="font-family:'DISPLAY_FONT',sans-serif;font-size:1.4rem;font-weight:800;color:var(--text-light);">TRUST_STAT_3</div>
        <div style="font-size:12px;color:var(--text-muted);letter-spacing:0.04em;">TRUST_LABEL_3</div>
      </div>
    </div>
  </div>
</section>

<!-- â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• ABOUT â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• -->
<section id="about" class="section-dark" style="padding:100px 32px;">
  <div style="max-width:1000px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:64px;align-items:center;">
    <!-- Text column -->
    <div>
      <p style="font-size:11px;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:var(--primary);margin-bottom:16px;">ABOUT_SECTION_LABEL</p>
      <h2 class="font-display" style="font-size:clamp(1.8rem,3.5vw,2.6rem);font-weight:800;color:var(--text-light);line-height:1.15;margin-bottom:24px;">
        ABOUT_HEADLINE
      </h2>
      <p style="font-size:1rem;line-height:1.85;color:var(--text-muted);margin-bottom:20px;">ABOUT_PARAGRAPH_1</p>
      <p style="font-size:1rem;line-height:1.85;color:var(--text-muted);">ABOUT_PARAGRAPH_2</p>
    </div>
    <!-- Icon / visual column â€” Phosphor icons only -->
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
      <div class="card" style="text-align:center;padding:28px 20px;">
        <i class="ph ph-VALUE_ICON_1" style="font-size:36px;color:var(--primary);display:block;margin-bottom:12px;"></i>
        <div style="font-family:'DISPLAY_FONT',sans-serif;font-size:.9rem;font-weight:700;color:var(--text-light);">VALUE_1</div>
      </div>
      <div class="card" style="text-align:center;padding:28px 20px;">
        <i class="ph ph-VALUE_ICON_2" style="font-size:36px;color:var(--secondary);display:block;margin-bottom:12px;"></i>
        <div style="font-family:'DISPLAY_FONT',sans-serif;font-size:.9rem;font-weight:700;color:var(--text-light);">VALUE_2</div>
      </div>
      <div class="card" style="text-align:center;padding:28px 20px;">
        <i class="ph ph-VALUE_ICON_3" style="font-size:36px;color:var(--primary);display:block;margin-bottom:12px;"></i>
        <div style="font-family:'DISPLAY_FONT',sans-serif;font-size:.9rem;font-weight:700;color:var(--text-light);">VALUE_3</div>
      </div>
      <div class="card" style="text-align:center;padding:28px 20px;">
        <i class="ph ph-VALUE_ICON_4" style="font-size:36px;color:var(--secondary);display:block;margin-bottom:12px;"></i>
        <div style="font-family:'DISPLAY_FONT',sans-serif;font-size:.9rem;font-weight:700;color:var(--text-light);">VALUE_4</div>
      </div>
    </div>
  </div>
</section>

<!-- â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• FEATURES â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• -->
<section id="features" class="section-surface" style="padding:100px 32px;">
  <div style="max-width:1000px;margin:0 auto;">
    <div style="text-align:center;margin-bottom:64px;">
      <p style="font-size:11px;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:var(--primary);margin-bottom:12px;">FEATURES_SECTION_LABEL</p>
      <h2 class="font-display" style="font-size:clamp(1.8rem,3.5vw,2.6rem);font-weight:800;color:var(--text-light);line-height:1.15;">FEATURES_HEADLINE</h2>
    </div>

    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:24px;">

      <!-- Feature card 1 -->
      <div class="card">
        <div style="width:52px;height:52px;border-radius:16px;background:rgba(PRIMARY_RGB,0.12);border:1px solid rgba(PRIMARY_RGB,0.2);display:flex;align-items:center;justify-content:center;margin-bottom:20px;">
          <i class="ph ph-FEATURE_ICON_1" style="font-size:26px;color:var(--primary);"></i>
        </div>
        <h3 style="font-family:'DISPLAY_FONT',sans-serif;font-size:1.05rem;font-weight:700;color:var(--text-light);margin-bottom:10px;">FEATURE_TITLE_1</h3>
        <p style="font-size:.88rem;line-height:1.75;color:var(--text-muted);">FEATURE_DESC_1 in two compelling sentences about what makes this feature valuable.</p>
      </div>

      <!-- Feature card 2 -->
      <div class="card">
        <div style="width:52px;height:52px;border-radius:16px;background:rgba(SECONDARY_RGB,0.1);border:1px solid rgba(SECONDARY_RGB,0.18);display:flex;align-items:center;justify-content:center;margin-bottom:20px;">
          <i class="ph ph-FEATURE_ICON_2" style="font-size:26px;color:var(--secondary);"></i>
        </div>
        <h3 style="font-family:'DISPLAY_FONT',sans-serif;font-size:1.05rem;font-weight:700;color:var(--text-light);margin-bottom:10px;">FEATURE_TITLE_2</h3>
        <p style="font-size:.88rem;line-height:1.75;color:var(--text-muted);">FEATURE_DESC_2 in two compelling sentences about what makes this feature valuable.</p>
      </div>

      <!-- Feature card 3 -->
      <div class="card">
        <div style="width:52px;height:52px;border-radius:16px;background:rgba(PRIMARY_RGB,0.12);border:1px solid rgba(PRIMARY_RGB,0.2);display:flex;align-items:center;justify-content:center;margin-bottom:20px;">
          <i class="ph ph-FEATURE_ICON_3" style="font-size:26px;color:var(--primary);"></i>
        </div>
        <h3 style="font-family:'DISPLAY_FONT',sans-serif;font-size:1.05rem;font-weight:700;color:var(--text-light);margin-bottom:10px;">FEATURE_TITLE_3</h3>
        <p style="font-size:.88rem;line-height:1.75;color:var(--text-muted);">FEATURE_DESC_3 in two compelling sentences about what makes this feature valuable.</p>
      </div>

      <!-- Feature card 4 -->
      <div class="card">
        <div style="width:52px;height:52px;border-radius:16px;background:rgba(SECONDARY_RGB,0.1);border:1px solid rgba(SECONDARY_RGB,0.18);display:flex;align-items:center;justify-content:center;margin-bottom:20px;">
          <i class="ph ph-FEATURE_ICON_4" style="font-size:26px;color:var(--secondary);"></i>
        </div>
        <h3 style="font-family:'DISPLAY_FONT',sans-serif;font-size:1.05rem;font-weight:700;color:var(--text-light);margin-bottom:10px;">FEATURE_TITLE_4</h3>
        <p style="font-size:.88rem;line-height:1.75;color:var(--text-muted);">FEATURE_DESC_4 in two compelling sentences about what makes this feature valuable.</p>
      </div>

      <!-- Feature card 5 -->
      <div class="card">
        <div style="width:52px;height:52px;border-radius:16px;background:rgba(PRIMARY_RGB,0.12);border:1px solid rgba(PRIMARY_RGB,0.2);display:flex;align-items:center;justify-content:center;margin-bottom:20px;">
          <i class="ph ph-FEATURE_ICON_5" style="font-size:26px;color:var(--primary);"></i>
        </div>
        <h3 style="font-family:'DISPLAY_FONT',sans-serif;font-size:1.05rem;font-weight:700;color:var(--text-light);margin-bottom:10px;">FEATURE_TITLE_5</h3>
        <p style="font-size:.88rem;line-height:1.75;color:var(--text-muted);">FEATURE_DESC_5 in two compelling sentences about what makes this feature valuable.</p>
      </div>

      <!-- Feature card 6 -->
      <div class="card">
        <div style="width:52px;height:52px;border-radius:16px;background:rgba(SECONDARY_RGB,0.1);border:1px solid rgba(SECONDARY_RGB,0.18);display:flex;align-items:center;justify-content:center;margin-bottom:20px;">
          <i class="ph ph-FEATURE_ICON_6" style="font-size:26px;color:var(--secondary);"></i>
        </div>
        <h3 style="font-family:'DISPLAY_FONT',sans-serif;font-size:1.05rem;font-weight:700;color:var(--text-light);margin-bottom:10px;">FEATURE_TITLE_6</h3>
        <p style="font-size:.88rem;line-height:1.75;color:var(--text-muted);">FEATURE_DESC_6 in two compelling sentences about what makes this feature valuable.</p>
      </div>

    </div>
  </div>
</section>

<!-- â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• CTA / CONTACT â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• -->
<section id="contact" class="section-dark" style="padding:100px 32px;text-align:center;position:relative;overflow:hidden;">
  <div style="position:absolute;inset:0;pointer-events:none;background:radial-gradient(ellipse 70% 50% at 50% 50%, rgba(PRIMARY_RGB,0.12) 0%, transparent 65%);"></div>
  <div style="max-width:640px;margin:0 auto;position:relative;z-index:1;">
    <i class="ph ph-CTA_ICON" style="font-size:48px;color:var(--primary);display:block;margin-bottom:24px;"></i>
    <h2 class="font-display g-text" style="font-size:clamp(2rem,4vw,3rem);font-weight:800;line-height:1.1;margin-bottom:20px;">
      CTA_HEADLINE
    </h2>
    <p style="font-size:1.05rem;line-height:1.8;color:var(--text-muted);margin-bottom:44px;">
      CTA_SUBTEXT â€” two sentences reinforcing the value and inviting action.
    </p>
    <a href="mailto:CONTACT_EMAIL" class="btn-primary">
      <i class="ph ph-envelope" style="font-size:18px;"></i>
      CTA_BUTTON_TEXT
    </a>
  </div>
</section>

<!-- â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• FOOTER â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• -->
<footer class="section-surface" style="padding:48px 32px;text-align:center;border-top:1px solid rgba(PRIMARY_RGB,0.1);">
  <div style="display:flex;align-items:center;justify-content:center;gap:10px;margin-bottom:12px;">
    <i class="ph ph-FOOTER_ICON" style="font-size:20px;color:var(--primary);"></i>
    <span style="font-family:'DISPLAY_FONT',sans-serif;font-size:15px;font-weight:800;color:var(--text-light);">BRAND NAME</span>
  </div>
  <p style="font-size:13px;color:var(--text-muted);margin-bottom:8px;">BRAND_TAGLINE_FULL</p>
  <p style="font-size:12px;color:var(--text-muted);opacity:0.5;">Â© CURRENT_YEAR BRAND NAME. All rights reserved.</p>
</footer>

</body>
</html>
```

=== END GOLD-STANDARD REFERENCE ===
REPLACE every PLACEHOLDER (BRAND NAME, PRIMARY_HEX, FEATURE_ICON_*, etc.) with real,
brand-specific content derived from the user's business description.
Invent a palette â€” pick hex codes from the colour guide above.
Derive PRIMARY_RGB / SECONDARY_RGB from those hex codes (e.g. #c9a84c â†’ 201,168,76).
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


# ── Model priority lists ────────────────────────────────────────────────────────
# Each entry: (model_id, max_tokens)
# Groq models each have SEPARATE daily token pools — exhausting one doesn't
# affect the others.
# deepseek-r1-distill-llama-70b was decommissioned by Groq on 2025-07-31 — removed.
# IBM Watsonx commented out until monthly quota resets.

# Agent 1 — PlatformEngineer: needs large output for full HTML pages
_SITE_MODELS = [
    ("groq/llama-3.3-70b-versatile",           16000),  # primary — best quality
    ("groq/llama-3.1-8b-instant",               8000),  # 2nd — separate pool, very fast
    ("groq/llama-3.1-70b-versatile",           16000),  # 3rd — separate pool, high quality
    ("groq/gemma2-9b-it",                       8000),  # 4th — separate pool, reliable
    # ("watsonx/meta-llama/llama-3-3-70b-instruct", 16000),  # re-enable when IBM quota resets
]

# Agent 2 — EthicalStrategyDirector: deepest reasoning first
_CHAT_MODELS = [
    ("groq/llama-3.3-70b-versatile",           16000),  # primary — best instruction-following
    ("groq/llama-3.1-8b-instant",               8000),  # 2nd — 500k TPD safety net
    ("groq/llama-3.1-70b-versatile",           16000),  # 3rd — separate pool, high quality
    ("groq/gemma2-9b-it",                       8000),  # 4th — separate pool, reliable
    # ("watsonx/meta-llama/llama-3-3-70b-instruct", 16000),  # re-enable when IBM quota resets
]


def _build_llm(model: str, max_tokens: int) -> LLM:
    """
    Build a crewai LLM instance.
    Detects IBM Watsonx models by the 'watsonx/' prefix.
    """
    if model.startswith("watsonx/"):
        ibm_key = os.environ.get("IBM_API_KEY", "").strip()
        if not ibm_key:
            raise RuntimeError(
                "IBM Watsonx fallback triggered but IBM_API_KEY is not set. "
                "Add IBM_API_KEY, IBM_PROJECT_ID, and IBM_URL to backend/.env"
            )
        logger.info("Using IBM Watsonx fallback model=%s (max_tokens=%d)", model, max_tokens)
        return LLM(
            model=model,
            base_url=os.environ.get("IBM_URL", "https://us-south.ml.cloud.ibm.com"),
            api_key=ibm_key,
            project_id=os.environ.get("IBM_PROJECT_ID", ""),
            temperature=0.6,
            max_tokens=max_tokens,
        )

    groq_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not groq_key:
        raise RuntimeError(
            "GROQ_API_KEY is not set and IBM Watsonx fallback was also unavailable. "
            "Add GROQ_API_KEY or IBM_API_KEY to backend/.env"
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
    Return True for errors that mean 'this model is unavailable — try the next one'.
    Covers: rate limits, quota exhaustion, decommissioned/deleted models, invalid model IDs.
    """
    markers = (
        # Rate limit / quota
        "rate_limit_exceeded", "ratelimiterror", "429", "too many requests",
        "token_quota_reached", "quota", "exceeded",
        # IBM Watsonx quota / auth issues — treat as skippable so Groq still runs
        "watsonxexception", "403",
        # Model decommissioned / not found
        "decommissioned", "model_decommissioned", "does not exist",
        "model not found", "invalid model", "no such model", "not supported",
        # Generic bad request from any provider
        "bad request",
    )
    low = err_str.lower()
    return any(m.lower() in low for m in markers)


def _run_with_fallback(task_factory, model_list: list) -> str:
    """
    Try each model in model_list in order.
    Skips to the next model on rate limits, quota errors, and unavailable models.
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
        except Exception as e:
            err_str = str(e)
            if _is_skippable_error(err_str):
                logger.warning(
                    "Skipping %s (%s) — trying next model.",
                    model, err_str[:200],
                )
                last_err = e
                time.sleep(2)   # give the API a moment before retrying next model
                continue
            # Unexpected error — log and re-raise immediately
            logger.error("Non-skippable error on %s: %s", model, err_str[:300])
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
            "You are a world-class UI/UX designer and senior frontend engineer with 15+ years "
            "building high-converting landing pages for brands across the Middle East, Southeast "
            "Asia, and Africa. You speak the visual language of every culture â€” you write "
            "RTL-ready Arabic layouts as fluently as LTR English ones. You configure Tailwind's "
            "theme block to register the brand's exact hex codes and font names so every class "
            "in the generated page uses the real brand identity. You never use Lorem ipsum, "
            "never use placeholder images, and never leave a section empty.\n\n"
            "You are fluent in glassmorphism, gradient-rich dark themes, and micro-interaction "
            "design. For ALL icons and decorative graphics you exclusively use Phosphor Icons "
            "(<i class=\"ph ph-*\"> tags from the Phosphor CDN). "
            "You NEVER write raw SVG shapes from scratch.\n\n"
            "You ALWAYS invent a fresh, industry-specific colour palette for every project. "
            "You NEVER reuse the same palette twice. You NEVER default to emerald or slate. "
            "The palette is always driven by the brand's industry and cultural context.\n\n"
            "â˜… CRITICAL LANGUAGE INSTRUCTION â˜…\n"
            "You are a native speaker of every language. You MUST detect the language of the "
            "user's prompt (e.g., Arabic, French, Spanish, Hindi). Your ENTIRE response â€” "
            "including all generated HTML website copy, section headings, CTA buttons, footer "
            "text, and any chat messages â€” MUST be written in that EXACT same language. "
            "Do NOT default to English. "
            "If the language is Arabic, Hebrew, Farsi, Urdu, or any other RTL script, "
            "you MUST wrap the HTML in <html lang=\"ar\" dir=\"rtl\"> "
            "(use the correct BCP-47 language tag) and mirror the entire layout for "
            "right-to-left reading."
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
            "â˜… CRITICAL LANGUAGE INSTRUCTION â˜…\n"
            f"The user's prompt language is: {language}. "
            "Your ENTIRE response â€” every word of HTML copy, every heading, button, "
            "paragraph, nav link, footer line â€” MUST be written in this language. "
            "Do NOT produce any English text unless the detected language IS English. "
            "If the language is Arabic or any RTL language, you MUST wrap the HTML in "
            f"{html_tag}.\n\n"
            f"Create a stunning, professional landing page for this business:\n\n"
            f"{business_description}\n\n"
            f"Page language: {language}. {rtl_note}\n\n"
            "=== ICONS & GRAPHICS (MANDATORY) ===\n"
            f"{_SVG_BAN}\n"
            f"âœ… Always include this in <head>:\n    {_PHOSPHOR_LINK}\n"
            f"âœ… Icon usage: {_PHOSPHOR_USAGE_EXAMPLE}\n"
            "Use ph-* icon names that match each feature's theme "
            "(ph-leaf, ph-lightning, ph-shield-check, ph-rocket, ph-heart, ph-star, "
            "ph-buildings, ph-graduation-cap, ph-stethoscope, ph-chart-line, ph-users, etc.)\n\n"
            "=== DYNAMIC PALETTE MANDATE ===\n"
            "âš ï¸  NEVER use emerald, slate, or any previously used colour scheme. "
            "You MUST invent a UNIQUE palette for this specific brand based on its industry "
            "and cultural context. Commit fully to that palette across every section. "
            "Register hex codes in tailwind.config AND as CSS --variables in :root {}.\n\n"
            f"{_TAILWIND_EXCELLENCE}\n\n"
            f"{_GOLD_SCAFFOLD}\n\n"
            "=== TECHNICAL REQUIREMENTS ===\n"
            "- DOCTYPE: <!DOCTYPE html> â€” full document, no fragments\n"
            "- Tailwind CSS via CDN: <script src='https://cdn.tailwindcss.com'></script>\n"
            f"- Phosphor Icons via CDN (in <head>): {_PHOSPHOR_LINK}\n"
            "- Google Fonts via @import inside a <style> block (select 2 fonts that suit the brand)\n"
            "- Register brand colours in tailwind.config + CSS :root {} variables\n"
            "- Smooth scroll: html { scroll-behavior: smooth; }\n"
            "- All nav links: in-page anchors only (href='#section-id') â€” NO external URLs\n"
            "- Mobile-first responsive layout with sm: md: lg: breakpoints\n\n"
            "=== REQUIRED SECTIONS (in order, each with a DIFFERENT background) ===\n"
            "1. STICKY NAV: brand logo/name + icon left (or right for RTL), nav links opposite side\n"
            "2. HERO (id='hero'): min-h-screen, large headline (text-5xlâ€“text-7xl), subheadline, "
            "   CTA button, radial CSS glow â€” no images, no raw SVG\n"
            "3. TRUST BAR: 3â€“4 factual trust signals from the business description only\n"
            "4. ABOUT (id='about'): brand story + 2x2 value cards â€” DIFFERENT bg from hero\n"
            "5. FEATURES (id='features'): 6 glassmorphism cards with Phosphor Icons â€” "
            "   DIFFERENT bg from about\n"
            "6. CTA / CONTACT (id='contact'): bold headline + subtext + primary button\n"
            "7. FOOTER: brand name + tagline + Â© year â€” DIFFERENT bg tone from CTA\n\n"
            "=== STRICT RULES ===\n"
            "- NEVER use Lorem ipsum â€” all copy must be brand-specific\n"
            "- NEVER use <img> tags or external image URLs\n"
            "- NEVER write <svg>, <path>, <circle>, or any raw SVG shape tags\n"
            "- NEVER include testimonials with invented quotes/names\n"
            "- NEVER display star ratings or invented counts\n"
            "- CTA text must be action-oriented â€” never 'Click Here'\n\n"
            "OUTPUT: Return ONLY the complete HTML document. "
            "No markdown fences. No explanation. Start with <!DOCTYPE html>."
        ),
        agent=agent,
        expected_output=(
            f"A complete <!DOCTYPE html> document with {html_tag} that exactly follows "
            "the gold-standard scaffold structure â€” fully styled with Tailwind CSS and "
            "Phosphor Icons (NO raw SVG), all seven required sections with ALTERNATING "
            f"background colours, all copy written entirely in '{language}' "
            "(NOT defaulted to English), a UNIQUE industry-specific colour palette "
            "(not emerald/slate), real brand-specific content, no placeholder text, "
            "no fake reviews, RTL-correct layout if applicable, "
            "professional award-winning visual design."
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
            "You are a legendary brand strategist AND visual identity designer â€” a modern "
            "Hakawati (Arabic storyteller) who has built category-defining brands across "
            "fashion, tech, food, wellness, and community-driven businesses in the Middle "
            "East, Africa, and Southeast Asia. You combine McKinsey-level strategic thinking "
            "with the visual craft of Pentagram's finest partners.\n\n"
            "â˜… LOGO DESIGN MASTERY â˜…\n"
            "You have designed logos for Fortune 500 companies. You know that a great logo "
            "is a SYSTEM â€” symbol mark + wordmark + lockup â€” not just an icon in a box. "
            "You study and reference the craft principles behind Google (clean wordmark, "
            "geometric precision), Microsoft (four-colour grid symbol), Amazon (smile arc "
            "as brand gesture), Nike (pure abstracted motion), Airbnb (human warmth in "
            "rounded forms), and Apple (geometric minimalism). "
            "Your symbol marks are built from layered CSS div shapes (border-radius, "
            "clip-path, transform:rotate, box-shadow) with a Phosphor icon as the semantic "
            "nucleus. They are NEVER just 'initials in a rounded square'. "
            "Your wordmarks use carefully chosen Google Fonts with custom tracking, weight, "
            "and selective colour on ONE accent letter to create a signature moment. "
            "Every logo is shown in a complete identity sheet: isolated symbol at multiple "
            "sizes (scalability test), isolated wordmark dark+light, full lockup on dark "
            "background / light background / brand-colour background, and a colour system "
            "bar with proper hex codes and usage labels.\n\n"
            "â˜… SOCIAL MEDIA CONTENT MASTERY â˜…\n"
            "You have crafted social media content for Apple, Spotify, Nike, and Glossier. "
            "For social media post requests you do NOT generate any HTML or visual code. "
            "Instead, you deliver a complete, ready-to-use CONTENT PACK as structured text:\n"
            "  â€¢ 3 post copy variants (each with a headline, body text, and hashtag set)\n"
            "  â€¢ For each post: a detailed photo/image description the user can search for "
            "    on Unsplash, Pexels, or their own photo library\n"
            "Your post copy is punchy, platform-native, and ethical â€” no fake scarcity, "
            "no FOMO. Every variant has a distinct tone and purpose:\n"
            "  Post 1 (Hero): bold brand-defining announcement or core value statement\n"
            "  Post 2 (Value/Feature): educational, highlights a key benefit or feature\n"
            "  Post 3 (Community/Story): warm, personal, community-first message\n"
            "Photo descriptions are specific and visual â€” enough for the user to confidently "
            "search or brief a photographer (lighting, composition, subject, mood, colour tone).\n\n"
            "â˜… CRITICAL LANGUAGE INSTRUCTION â˜…\n"
            "You are a native speaker of every language. You MUST detect the language of the "
            "user's prompt (e.g., Arabic, French, Spanish, Hindi, Turkish). Your ENTIRE "
            "response â€” including all strategic advice, HTML website copy, visual artifact text, "
            "labels, headings, and chat messages â€” MUST be written in that EXACT same language. "
            "Do NOT default to English. "
            "If the language is Arabic or any RTL language, you MUST wrap the HTML in "
            "<html lang=\"ar\" dir=\"rtl\"> and mirror all layouts for right-to-left reading.\n\n"
            "ðŸš¨ HARD ETHICAL GUARDRAILS â€” ZERO TOLERANCE ðŸš¨\n"
            "You are bound by strict, honest, and modest business principles (avoiding "
            "Gharar/deception). If a user explicitly asks you to create 'fake scarcity', "
            "'panic buying', 'FOMO', or lie about stock levels, YOU MUST REFUSE. "
            "Do NOT provide the unethical strategy under any circumstances. "
            "Instead, you must immediately pivot: politely explain â€” in the user's exact language "
            "â€” that this violates transparent business practices and honest dealing principles. "
            "Then outline a concrete, value-driven alternative campaign that focuses on honesty, "
            "genuine quality, and authentic customer relationships. "
            "This ethical rule applies unconditionally across ALL languages, including Arabic, "
            "French, Spanish, and every other language a user may write in. "
            "There are NO exceptions and NO workarounds to this rule."
        ),
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )


# â”€â”€ Per-artifact-type gold scaffolds â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# These are injected into make_chat_task when the message requests that artifact.
# Concrete templates produce dramatically better output than written rules alone.

_ARTIFACT_LOGO = """
=== PROFESSIONAL LOGO IDENTITY SYSTEM â€” GOLD-STANDARD SCAFFOLD ===

You are a world-class identity designer at the level of the firms that created the logos
for Google, Microsoft, Amazon, Apple, Nike, and Airbnb.  Your output must be a complete,
multi-format brand identity presentation â€” NOT a simple icon in a box.

A professional logo system has FOUR components shown in one polished HTML page:
  1. SYMBOL MARK   â€” a distinctive geometric/abstract icon (CSS shapes + Phosphor Icons, no raw SVG paths)
  2. WORDMARK      â€” the brand name set in a carefully chosen, custom-configured typeface
  3. LOCKUP        â€” symbol + wordmark combined horizontally, the primary logo
  4. USAGE SHEET   â€” the lockup shown on dark bg, light bg, and a colour-accent bg + colour bar

DESIGN PHILOSOPHY â€” study how world-class logos work:
  â€¢ Google: clean wordmark, multi-colour, highly legible, geometric letterforms
  â€¢ Microsoft: four-coloured grid symbol, clean Segoe wordmark beside it
  â€¢ Amazon: wordmark with a distinctive smile underline arc as the symbol element
  â€¢ Nike: pure symbol (swoosh) â€” abstracted motion, one colour, timeless
  â€¢ Airbnb: custom rounded symbol + rounded wordmark, warm coral, feels human
  â€¢ Apple: geometric symbol (bitten circle) + clean Helvetica wordmark

Your logo symbol MUST be:
  â€¢ Built from CSS border-radius, clip-path, and layered div shapes â€” NO raw <svg>/<path> tags
  â€¢ Distinctive and UNIQUE to this brand's industry and personality
  â€¢ Scalable â€” looks great from 24px favicon to 400px hero size
  â€¢ The symbol is NOT just "initials in a rounded square" â€” it must be a REAL abstract mark
  â€¢ Use layered CSS divs, rotations, clip-paths, and Phosphor icon at the centre as the nucleus

WORDMARK rules:
  â€¢ Choose a Google-Fonts typeface that defines the brand personality
  â€¢ Apply custom letter-spacing, font-weight, and selective colour on ONE letter or ligature
  â€¢ The wordmark alone must be instantly recognisable

Produce an HTML page at EXACTLY this quality level, replacing every PLACEHOLDER:

```html
<!DOCTYPE html>
<html lang="LANG" dir="DIR">
<head>
  <meta charset="UTF-8" /><meta name="viewport" content="width=device-width,initial-scale=1"/>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" type="text/css" href="https://unpkg.com/@phosphor-icons/web@2.1.1/src/regular/style.css"/>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=WORDMARK_FONT:wght@300;400;600;700;800;900&family=UI_FONT:wght@400;500;600&display=swap');

    *, *::before, *::after { box-sizing:border-box; margin:0; padding:0; }
    html { background:#CANVAS_BG_HEX; }   /* e.g. #f2f2f5 â€” neutral canvas */
    body { font-family:'UI_FONT', sans-serif; color:#1a1a2e; }

    /* â”€â”€ Brand token system â”€â”€ */
    :root {
      --primary:   #PRIMARY_HEX;   /* e.g. the dominant brand colour */
      --secondary: #SECONDARY_HEX; /* e.g. supporting accent */
      --dark:      #DARK_HEX;      /* near-black base for dark bg previews */
      --light:     #LIGHT_HEX;     /* near-white for light bg previews */
      --accent:    #ACCENT_HEX;    /* pop colour â€” used sparingly */
      /* Derive RGB triplets from the hex values above for use in rgba() */
      --p-rgb: PRIMARY_R, PRIMARY_G, PRIMARY_B;
      --s-rgb: SECONDARY_R, SECONDARY_G, SECONDARY_B;
      --a-rgb: ACCENT_R, ACCENT_G, ACCENT_B;
    }

    /* â”€â”€ Symbol mark â€” the geometric abstract icon â”€â”€ */
    /* This is the heart of the logo. Build it purely from CSS shapes:
       layered divs, border-radius, clip-path, transforms, box-shadows.
       A Phosphor icon sits at the nucleus as the semantic anchor.
       Replace the class body below with your actual construction.       */
    .symbol {
      width: var(--sym-size, 80px);
      height: var(--sym-size, 80px);
      position: relative;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }
    /* Outer shape â€” e.g. a bold rounded square, circle, or clipped polygon */
    .symbol-outer {
      position: absolute; inset: 0;
      background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
      border-radius: OUTER_RADIUS;   /* e.g. 22px for rounded-sq, 50% for circle, 0 for diamond */
      /* Optional rotation for a dynamic angle: transform: rotate(45deg); */
    }
    /* Inner accent layer â€” creates depth and a sense of craft */
    .symbol-inner {
      position: absolute;
      width: 58%; height: 58%;
      border-radius: INNER_RADIUS;
      background: rgba(var(--a-rgb), 0.22);
      border: 2px solid rgba(255,255,255, 0.30);
    }
    /* The Phosphor icon nucleus â€” semantic heart of the mark */
    .symbol-icon {
      position: relative; z-index: 2;
      font-size: calc(var(--sym-size, 80px) * 0.36);
      color: #ffffff;
    }

    /* â”€â”€ Wordmark â€” the typographic identity â”€â”€ */
    .wordmark {
      font-family: 'WORDMARK_FONT', sans-serif;
      font-weight: WORDMARK_WEIGHT;   /* e.g. 700 or 800 */
      font-size: var(--wm-size, 2rem);
      letter-spacing: WORDMARK_TRACKING;  /* e.g. -0.03em tight, 0.08em wide */
      color: var(--wm-color, var(--dark));
      line-height: 1;
      white-space: nowrap;
    }
    /* Selective accent â€” colour ONE letter or letter-pair to create a signature moment */
    .wordmark .accent-letter { color: var(--primary); }

    /* â”€â”€ Lockup â€” symbol + wordmark â”€â”€ */
    .lockup {
      display: inline-flex;
      align-items: center;
      gap: calc(var(--sym-size, 80px) * 0.22);
    }

    /* â”€â”€ Tagline / descriptor â”€â”€ */
    .tagline {
      font-size: 0.62rem;
      font-weight: 600;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: var(--tagline-color, rgba(var(--p-rgb), 0.7));
      margin-top: 5px;
    }

    /* â”€â”€ Section helpers â”€â”€ */
    .preview-panel {
      border-radius: 24px;
      padding: 52px 48px;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 28px;
    }
    .section-label {
      font-size: 10px; font-weight: 700; letter-spacing: .14em;
      text-transform: uppercase; color: #999; margin-bottom: 14px;
    }
    .divider { width: 100%; height: 1px; background: rgba(0,0,0,0.07); margin: 8px 0; }
    .size-row { display: flex; align-items: center; gap: 28px; flex-wrap: wrap; }

    /* â”€â”€ Colour bar â”€â”€ */
    .colour-bar {
      display: flex; border-radius: 18px; overflow: hidden;
      box-shadow: 0 6px 28px rgba(0,0,0,0.14);
    }
    .colour-swatch {
      flex: 1; padding: 18px 20px;
      display: flex; flex-direction: column; gap: 4px;
    }
    .swatch-name  { font-size: 10px; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: rgba(255,255,255,.55); }
    .swatch-hex   { font-family: monospace; font-size: 13px; font-weight: 700; color: rgba(255,255,255,.9); }
    .swatch-usage { font-size: 9px; color: rgba(255,255,255,.4); letter-spacing: .05em; }
  </style>
</head>
<body style="min-height:100vh; padding:56px 24px; background:#CANVAS_BG_HEX;">
<div style="max-width:960px; margin:0 auto; display:flex; flex-direction:column; gap:56px;">

  <!-- â•â• PAGE HEADER â•â• -->
  <div>
    <p class="section-label">Brand Identity System</p>
    <h1 style="font-family:'WORDMARK_FONT',sans-serif;font-size:2rem;font-weight:800;color:#1a1a2e;line-height:1.1;margin-bottom:8px;">
      BRAND_NAME â€” Logo Identity
    </h1>
    <p style="font-size:.9rem;color:#777;max-width:500px;line-height:1.7;">
      BRAND_POSITIONING_SENTENCE â€” one sentence that captures what this brand stands for and who it serves.
    </p>
  </div>

  <!-- â•â• SYMBOL MARK (isolated) â•â• -->
  <div>
    <p class="section-label">Symbol Mark</p>
    <div style="display:flex;flex-wrap:wrap;gap:40px;align-items:flex-end;">
      <!-- XL symbol alone on neutral -->
      <div style="background:#fff;border-radius:20px;padding:40px;border:1px solid #eaeaf0;display:inline-flex;align-items:center;justify-content:center;">
        <div class="symbol" style="--sym-size:120px;">
          <div class="symbol-outer"></div>
          <div class="symbol-inner"></div>
          <i class="ph ph-BRAND_ICON symbol-icon"></i>
        </div>
      </div>
      <!-- Symbol at multiple sizes â€” scalability test -->
      <div class="size-row" style="flex-direction:column;align-items:flex-start;gap:20px;">
        <p style="font-size:11px;color:#aaa;letter-spacing:.08em;text-transform:uppercase;font-weight:600;">Scalability</p>
        <div style="display:flex;align-items:center;gap:20px;">
          <div class="symbol" style="--sym-size:64px;"><div class="symbol-outer"></div><div class="symbol-inner"></div><i class="ph ph-BRAND_ICON symbol-icon"></i></div>
          <div class="symbol" style="--sym-size:40px;"><div class="symbol-outer"></div><div class="symbol-inner"></div><i class="ph ph-BRAND_ICON symbol-icon"></i></div>
          <div class="symbol" style="--sym-size:28px;"><div class="symbol-outer"></div><div class="symbol-inner"></div><i class="ph ph-BRAND_ICON symbol-icon"></i></div>
          <div class="symbol" style="--sym-size:18px;background:var(--primary);border-radius:5px;display:flex;align-items:center;justify-content:center;"><i class="ph ph-BRAND_ICON" style="font-size:10px;color:#fff;position:relative;z-index:2;"></i></div>
        </div>
        <p style="font-size:11px;color:#bbb;">64px Â· 40px Â· 28px Â· 18px favicon</p>
      </div>
    </div>
  </div>

  <!-- â•â• WORDMARK (isolated) â•â• -->
  <div>
    <p class="section-label">Wordmark</p>
    <div style="background:#fff;border-radius:20px;padding:40px 48px;border:1px solid #eaeaf0;display:flex;flex-direction:column;gap:24px;">
      <!-- Primary wordmark â€” dark on light -->
      <div>
        <p style="font-size:10px;color:#bbb;letter-spacing:.08em;text-transform:uppercase;font-weight:600;margin-bottom:14px;">Dark on Light</p>
        <div class="wordmark" style="--wm-size:3rem;--wm-color:var(--dark);">
          WORD<span class="accent-letter">MARK</span>
          <!-- Replace WORD and MARK with the actual split of the brand name.
               The accent-letter span wraps ONE distinctive letter or the last syllable. -->
        </div>
      </div>
      <div class="divider"></div>
      <!-- Reversed wordmark â€” light on dark -->
      <div style="background:var(--dark);border-radius:14px;padding:28px 32px;">
        <p style="font-size:10px;color:rgba(255,255,255,.3);letter-spacing:.08em;text-transform:uppercase;font-weight:600;margin-bottom:14px;">Light on Dark</p>
        <div class="wordmark" style="--wm-size:3rem;--wm-color:#ffffff;">
          WORD<span class="accent-letter">MARK</span>
        </div>
      </div>
    </div>
  </div>

  <!-- â•â• FULL LOCKUP (primary use) â•â• -->
  <div>
    <p class="section-label">Primary Lockup â€” Symbol + Wordmark</p>
    <div style="display:flex;flex-direction:column;gap:20px;">

      <!-- Dark background â€” primary presentation -->
      <div class="preview-panel" style="background:var(--dark);box-shadow:0 20px 56px rgba(0,0,0,0.35);">
        <div class="lockup" style="--sym-size:64px;">
          <div class="symbol"><div class="symbol-outer"></div><div class="symbol-inner"></div><i class="ph ph-BRAND_ICON symbol-icon"></i></div>
          <div>
            <div class="wordmark" style="--wm-size:2.2rem;--wm-color:#ffffff;">WORD<span class="accent-letter">MARK</span></div>
            <div class="tagline" style="--tagline-color:rgba(255,255,255,0.38);">BRAND_TAGLINE</div>
          </div>
        </div>
        <p style="font-size:10px;color:rgba(255,255,255,.25);letter-spacing:.1em;text-transform:uppercase;font-weight:600;">Dark Background Â· Primary Use</p>
      </div>

      <!-- Light background -->
      <div class="preview-panel" style="background:#ffffff;border:1px solid #eaeaf0;box-shadow:0 8px 28px rgba(0,0,0,0.07);">
        <div class="lockup" style="--sym-size:64px;">
          <div class="symbol"><div class="symbol-outer"></div><div class="symbol-inner"></div><i class="ph ph-BRAND_ICON symbol-icon"></i></div>
          <div>
            <div class="wordmark" style="--wm-size:2.2rem;--wm-color:var(--dark);">WORD<span class="accent-letter">MARK</span></div>
            <div class="tagline">BRAND_TAGLINE</div>
          </div>
        </div>
        <p style="font-size:10px;color:#ccc;letter-spacing:.1em;text-transform:uppercase;font-weight:600;">Light Background</p>
      </div>

      <!-- Brand-colour background -->
      <div class="preview-panel" style="background:var(--primary);box-shadow:0 12px 36px rgba(var(--p-rgb),0.45);">
        <div class="lockup" style="--sym-size:64px;">
          <div class="symbol">
            <div class="symbol-outer" style="background:rgba(255,255,255,0.18);border:2px solid rgba(255,255,255,0.35);"></div>
            <div class="symbol-inner" style="background:rgba(255,255,255,0.10);border-color:rgba(255,255,255,0.2);"></div>
            <i class="ph ph-BRAND_ICON symbol-icon" style="color:#fff;"></i>
          </div>
          <div>
            <div class="wordmark" style="--wm-size:2.2rem;--wm-color:#ffffff;">WORD<span class="accent-letter" style="color:rgba(255,255,255,0.65);">MARK</span></div>
            <div class="tagline" style="--tagline-color:rgba(255,255,255,0.5);">BRAND_TAGLINE</div>
          </div>
        </div>
        <p style="font-size:10px;color:rgba(255,255,255,.35);letter-spacing:.1em;text-transform:uppercase;font-weight:600;">Brand Colour Background</p>
      </div>

    </div>
  </div>

  <!-- â•â• COLOUR SYSTEM â•â• -->
  <div>
    <p class="section-label">Colour System</p>
    <div class="colour-bar">
      <div class="colour-swatch" style="background:var(--primary);">
        <span class="swatch-name">Primary</span>
        <span class="swatch-hex">#PRIMARY_HEX</span>
        <span class="swatch-usage">CTAs Â· Symbol Â· Key accent</span>
      </div>
      <div class="colour-swatch" style="background:var(--secondary);">
        <span class="swatch-name">Secondary</span>
        <span class="swatch-hex">#SECONDARY_HEX</span>
        <span class="swatch-usage">Gradient pair Â· Highlights</span>
      </div>
      <div class="colour-swatch" style="background:var(--accent);">
        <span class="swatch-name">Accent</span>
        <span class="swatch-hex">#ACCENT_HEX</span>
        <span class="swatch-usage">Inner ring Â· Contrast pop</span>
      </div>
      <div class="colour-swatch" style="background:var(--dark);">
        <span class="swatch-name">Base Dark</span>
        <span class="swatch-hex">#DARK_HEX</span>
        <span class="swatch-usage">Wordmark Â· Dark bg Â· Type</span>
      </div>
    </div>
  </div>

  <!-- â•â• TYPOGRAPHY â•â• -->
  <div>
    <p class="section-label">Typography</p>
    <div style="background:#fff;border-radius:20px;padding:36px 40px;border:1px solid #eaeaf0;display:flex;flex-direction:column;gap:16px;">
      <div>
        <p style="font-size:10px;color:#bbb;letter-spacing:.08em;font-weight:600;text-transform:uppercase;margin-bottom:8px;">Display / Wordmark â€” WORDMARK_FONT</p>
        <div style="font-family:'WORDMARK_FONT',sans-serif;font-size:2.4rem;font-weight:800;color:#1a1a2e;line-height:1.05;letter-spacing:WORDMARK_TRACKING;">BRAND_NAME Headlines</div>
      </div>
      <div class="divider"></div>
      <div>
        <p style="font-size:10px;color:#bbb;letter-spacing:.08em;font-weight:600;text-transform:uppercase;margin-bottom:8px;">Body â€” UI_FONT</p>
        <p style="font-family:'UI_FONT',sans-serif;font-size:1rem;color:#555;line-height:1.75;max-width:520px;">
          BRAND_POSITIONING_SENTENCE_FULL â€” two sentences that describe what the brand does, who it's for, and the promise it makes to its customers every single day.
        </p>
      </div>
    </div>
  </div>

</div>
</body></html>
```

=== IMPLEMENTATION INSTRUCTIONS ===
REPLACE every PLACEHOLDER token with real brand-specific values:
- BRAND_ICON       â†’ a Phosphor icon name that embodies the brand (e.g. ph-leaf, ph-lightning, ph-buildings, ph-heart, ph-rocket)
- OUTER_RADIUS     â†’ CSS border-radius for the symbol outer shape (e.g. 22px, 50%, or use clip-path for hexagons/diamonds)
- INNER_RADIUS     â†’ border-radius for the inner accent ring
- WORDMARK_FONT    â†’ Google Font for the wordmark (e.g. "Sora", "DM Sans", "Space Grotesk", "Outfit", "Plus Jakarta Sans")
- UI_FONT          â†’ Google Font for body/UI text
- WORDMARK_WEIGHT  â†’ font-weight (700, 800, or 900)
- WORDMARK_TRACKINGâ†’ letter-spacing (tight: -0.03em, normal: 0, wide: 0.06em)
- WORD / MARK      â†’ split the brand name so ONE part gets the accent colour (e.g. "Eco" + "Hub" â†’ <span class='accent-letter'>Hub</span>)
- PRIMARY_HEX etc. â†’ real hex codes derived from the industry palette guide
- PRIMARY_R/G/B etc.â†’ decimal RGB channels of the primary hex (for rgba() usage)
- CANVAS_BG_HEX    â†’ neutral canvas, e.g. #f2f2f5 or #f8f7f4 â€” NOT white
- All BRAND_* text  â†’ real brand content from the business description

The symbol-outer shape MUST be something other than a generic rounded square:
  - For tech/fintech: clip-path hexagon or sharp-edged diamond with one chamfered corner
  - For wellness/organic: full circle with an inner offset circle for depth
  - For luxury/fashion: a thin rectangular frame with a single diagonal cut
  - For food/cafÃ©: a rounded square tilted 45Â° (diamond) with warm gradient
  - For education: a layered shield or book-inspired trapezoid shape
  - The BRAND_ICON Phosphor icon at the centre gives it semantic meaning

This is a WORLD-CLASS logo presentation. Every pixel must be intentional.
"""

_ARTIFACT_PALETTE = """
=== COLOUR PALETTE â€” GOLD-STANDARD SCAFFOLD ===
Produce an HTML page that looks EXACTLY like this, with real brand colours.

```html
<!DOCTYPE html>
<html lang="LANG" dir="DIR">
<head>
  <meta charset="UTF-8" /><meta name="viewport" content="width=device-width,initial-scale=1"/>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" type="text/css" href="https://unpkg.com/@phosphor-icons/web@2.1.1/src/regular/style.css"/>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=DISPLAY_FONT:wght@700;800&family=BODY_FONT:wght@400;500&display=swap');
    body { margin:0; padding:48px 24px; background:#f8f8f8; font-family:'BODY_FONT',sans-serif; }
    .swatch { border-radius:20px; height:160px; position:relative; overflow:hidden; box-shadow:0 8px 32px rgba(0,0,0,0.12); }
    .swatch-label { position:absolute; bottom:0; left:0; right:0; padding:14px 18px; background:rgba(0,0,0,0.28); backdrop-filter:blur(8px); }
    .hex { font-family:monospace; font-size:12px; font-weight:700; letter-spacing:.06em; }
    .usage { font-size:10px; letter-spacing:.1em; text-transform:uppercase; opacity:.75; margin-top:2px; }
    h1 { font-family:'DISPLAY_FONT',sans-serif; font-weight:800; font-size:1.5rem; color:#1a1a2e; margin-bottom:6px; }
    .section-title { font-size:10px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#999;margin-bottom:20px; }
  </style>
</head>
<body>
<div style="max-width:820px;margin:0 auto;">
  <div style="margin-bottom:36px;">
    <p class="section-title">Brand Identity System</p>
    <h1>BRAND NAME â€” Colour Palette</h1>
    <p style="font-size:.9rem;color:#888;max-width:480px;line-height:1.7;">
      A carefully crafted palette for BRAND_INDUSTRY â€” built for trust, recognition, and emotional resonance.
    </p>
  </div>

  <!-- Primary swatches row -->
  <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:16px;margin-bottom:16px;">
    <div class="swatch" style="background:#COLOUR_1_HEX;">
      <div class="swatch-label"><div class="hex" style="color:#fff;">#COLOUR_1_HEX</div><div class="usage" style="color:rgba(255,255,255,.8);">Primary Â· USAGE_1</div></div>
    </div>
    <div class="swatch" style="background:#COLOUR_2_HEX;">
      <div class="swatch-label"><div class="hex" style="color:#fff;">#COLOUR_2_HEX</div><div class="usage" style="color:rgba(255,255,255,.8);">Secondary Â· USAGE_2</div></div>
    </div>
    <div class="swatch" style="background:#COLOUR_3_HEX;">
      <div class="swatch-label"><div class="hex" style="color:#fff;">#COLOUR_3_HEX</div><div class="usage" style="color:rgba(255,255,255,.8);">Accent Â· USAGE_3</div></div>
    </div>
    <div class="swatch" style="background:#COLOUR_4_HEX;">
      <div class="swatch-label"><div class="hex" style="color:#fff;">#COLOUR_4_HEX</div><div class="usage" style="color:rgba(255,255,255,.8);">Background Â· USAGE_4</div></div>
    </div>
  </div>

  <!-- Text / neutral row -->
  <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:16px;margin-bottom:40px;">
    <div class="swatch" style="background:#COLOUR_5_HEX;height:100px;">
      <div class="swatch-label"><div class="hex" style="color:#fff;">#COLOUR_5_HEX</div><div class="usage" style="color:rgba(255,255,255,.8);">Heading Text</div></div>
    </div>
    <div class="swatch" style="background:#COLOUR_6_HEX;height:100px;">
      <div class="swatch-label"><div class="hex" style="color:rgba(0,0,0,.6);">#COLOUR_6_HEX</div><div class="usage" style="color:rgba(0,0,0,.45);">Body Text</div></div>
    </div>
    <div class="swatch" style="background:#COLOUR_7_HEX;height:100px;border:1px solid #e0e0e0;">
      <div class="swatch-label"><div class="hex" style="color:rgba(0,0,0,.5);">#COLOUR_7_HEX</div><div class="usage" style="color:rgba(0,0,0,.4);">Surface / Card</div></div>
    </div>
  </div>

  <!-- Typography preview -->
  <div style="background:#fff;border-radius:20px;padding:36px;border:1px solid #eee;box-shadow:0 4px 20px rgba(0,0,0,.05);">
    <p class="section-title">Typography in Context</p>
    <h2 style="font-family:'DISPLAY_FONT',sans-serif;font-size:2rem;font-weight:800;color:#COLOUR_5_HEX;margin-bottom:8px;line-height:1.1;">DISPLAY_FONT â€” Brand Headline</h2>
    <p style="font-size:.95rem;line-height:1.8;color:#COLOUR_6_HEX;max-width:520px;">
      BODY_FONT in body text. Clear, confident, and perfectly legible â€” designed to communicate the essence of BRAND_INDUSTRY with precision.
    </p>
  </div>
</div>
</body></html>
```
=== Replace every COLOUR_N_HEX and PLACEHOLDER with the real brand palette values. ===
"""

_ARTIFACT_SOCIAL = """
=== SOCIAL MEDIA CONTENT PACK â€” TEXT + PHOTO GUIDE ===

You are a world-class social media strategist and copywriter.

For social media post requests you MUST deliver a plain-text CONTENT PACK.
Do NOT produce any HTML, CSS, or visual code.

Your output format (use exactly this structure, in the user's language):

---
## ðŸ“± Social Media Content Pack

### Post 1 â€” Hero / Brand Statement
**Headline:** [a punchy 5â€“10 word headline]
**Body copy:** [2â€“4 sentences â€” bold brand voice, core value proposition]
**Hashtags:** #tag1 #tag2 #tag3 #tag4 #tag5

**ðŸ“· Photo to find:**
[Specific visual description: subject, setting, lighting, mood, colour tone, composition.
e.g. "A close-up of golden honey dripping from a wooden dipper onto a white marble surface,
warm natural sidelight, shallow depth of field, rich amber tones â€” search 'honey drip marble'
on Unsplash or Pexels."]

---
### Post 2 â€” Value / Feature
**Headline:** [educational or benefit-focused headline]
**Body copy:** [2â€“4 sentences â€” highlight one key benefit or feature]
**Hashtags:** #tag1 #tag2 #tag3 #tag4 #tag5

**ðŸ“· Photo to find:**
[Specific visual description with search terms for Unsplash/Pexels/their own library.]

---
### Post 3 â€” Community / Story
**Headline:** [warm, personal, human-centred headline]
**Body copy:** [2â€“4 sentences â€” authentic, community-first tone, no FOMO]
**Hashtags:** #tag1 #tag2 #tag3 #tag4 #tag5

**ðŸ“· Photo to find:**
[Specific visual description with search terms for Unsplash/Pexels/their own library.]

---
## ðŸ’¡ Posting Tips
[2â€“3 short tips specific to this brand's audience and industry â€” best time to post,
caption length, platform-specific advice (Instagram vs LinkedIn vs Facebook).]
---

REPLACE every placeholder with real, brand-specific content derived from the business context.
Write entirely in the user's language. No HTML. No code fences. Pure text.
"""


_ARTIFACT_BIZCARD = """
=== BUSINESS CARD â€” GOLD-STANDARD SCAFFOLD ===
Produce an HTML page showing both sides of a professional business card (3.5Ã—2 inch at 2Ã—: 700Ã—400px each).

```html
<!DOCTYPE html>
<html lang="LANG" dir="DIR">
<head>
  <meta charset="UTF-8" /><meta name="viewport" content="width=device-width,initial-scale=1"/>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" type="text/css" href="https://unpkg.com/@phosphor-icons/web@2.1.1/src/regular/style.css"/>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=DISPLAY_FONT:wght@700;800&family=BODY_FONT:wght@300;400;500&display=swap');
    * { box-sizing:border-box; margin:0; padding:0; }
    body { background:#d8d8e0; display:flex; align-items:center; justify-content:center; min-height:100vh; padding:48px 24px; font-family:'BODY_FONT',sans-serif; }
    :root { --p:#PRIMARY_HEX; --s:#SECONDARY_HEX; --b:#BASE_HEX; --tl:#TEXT_LIGHT_HEX; }
    .card-wrap { display:flex; flex-direction:column; align-items:center; gap:32px; }
    .card { width:700px; height:400px; border-radius:20px; overflow:hidden; box-shadow:0 24px 64px rgba(0,0,0,0.3); position:relative; }
    .label { font-size:11px; font-weight:700; letter-spacing:.1em; text-transform:uppercase; color:#888; margin-bottom:12px; text-align:center; }
    h1.page-title { font-family:'DISPLAY_FONT',sans-serif; font-size:1.4rem; font-weight:800; color:#1a1a2e; margin-bottom:32px; text-align:center; }
  </style>
</head>
<body>
<div class="card-wrap">
  <h1 class="page-title">BRAND NAME â€” Business Card</h1>

  <!-- FRONT -->
  <div>
    <p class="label">Front</p>
    <div class="card" style="background:var(--b);padding:44px 52px;display:flex;flex-direction:column;justify-content:space-between;">
      <!-- Glow -->
      <div style="position:absolute;inset:0;pointer-events:none;background:radial-gradient(ellipse 80% 70% at 15% 20%, rgba(PRIMARY_RGB,0.2) 0%, transparent 55%);"></div>
      <!-- Logo row -->
      <div style="display:flex;align-items:center;gap:14px;position:relative;z-index:1;">
        <div style="width:46px;height:46px;border-radius:13px;background:var(--p);display:flex;align-items:center;justify-content:center;box-shadow:0 0 20px rgba(PRIMARY_RGB,0.4);">
          <i class="ph ph-LOGO_ICON" style="font-size:22px;color:#fff;"></i>
        </div>
        <div>
          <div style="font-family:'DISPLAY_FONT',sans-serif;font-size:1.1rem;font-weight:800;color:var(--tl);line-height:1.1;">BRAND NAME</div>
          <div style="font-size:9px;color:rgba(255,255,255,.4);letter-spacing:.1em;text-transform:uppercase;">TAGLINE</div>
        </div>
      </div>
      <!-- Person details -->
      <div style="position:relative;z-index:1;">
        <div style="font-family:'DISPLAY_FONT',sans-serif;font-size:1.35rem;font-weight:800;color:var(--tl);margin-bottom:4px;">PERSON NAME</div>
        <div style="font-size:.8rem;color:var(--p);font-weight:600;letter-spacing:.04em;margin-bottom:16px;">JOB TITLE</div>
        <div style="display:flex;flex-direction:column;gap:5px;">
          <div style="display:flex;align-items:center;gap:8px;"><i class="ph ph-envelope" style="font-size:13px;color:rgba(255,255,255,.4);"></i><span style="font-size:.78rem;color:rgba(255,255,255,.55);">EMAIL@BRAND.COM</span></div>
          <div style="display:flex;align-items:center;gap:8px;"><i class="ph ph-phone" style="font-size:13px;color:rgba(255,255,255,.4);"></i><span style="font-size:.78rem;color:rgba(255,255,255,.55);">+PHONE_NUMBER</span></div>
          <div style="display:flex;align-items:center;gap:8px;"><i class="ph ph-globe" style="font-size:13px;color:rgba(255,255,255,.4);"></i><span style="font-size:.78rem;color:rgba(255,255,255,.55);">WWW.BRAND.COM</span></div>
        </div>
      </div>
    </div>
  </div>

  <!-- BACK -->
  <div>
    <p class="label">Back</p>
    <div class="card" style="background:var(--p);padding:44px 52px;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;">
      <div style="position:absolute;inset:0;background:radial-gradient(ellipse 80% 70% at 85% 80%, rgba(0,0,0,0.2) 0%, transparent 55%);pointer-events:none;"></div>
      <i class="ph ph-BACK_ICON" style="font-size:48px;color:rgba(255,255,255,.2);margin-bottom:20px;position:relative;z-index:1;"></i>
      <div style="font-family:'DISPLAY_FONT',sans-serif;font-size:1.7rem;font-weight:900;color:#fff;letter-spacing:-0.02em;margin-bottom:8px;position:relative;z-index:1;">BRAND NAME</div>
      <div style="font-size:.75rem;color:rgba(255,255,255,.55);letter-spacing:.14em;text-transform:uppercase;position:relative;z-index:1;">BRAND TAGLINE FULL</div>
    </div>
  </div>
</div>
</body></html>
```
=== Fill every PLACEHOLDER with real brand data. Derive PRIMARY_RGB from the hex. ===
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
            "     Symbol = layered CSS div shapes (border-radius/clip-path/rotate) + Phosphor nucleus. "
            "     Wordmark = precision Google Font + selective accent on 1 letter. NOT initials in a box.\n"
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

