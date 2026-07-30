"use client";

import { useState } from "react";
import ArtifactRenderer from "../components/ArtifactRenderer";
import StrategyChat from "../components/StrategyChat";

/* ─────────────────────────────────────────────────────────────────────────────
   DEFAULT LANDING PAGE
   • Auto-detects language direction via <html dir="auto">
   • Abstract geometric SVG hero — no literal product drawings
   • Glassmorphism cards, emerald/gold/violet palette
   • Multilingual-ready (copy in English as default scaffold)
───────────────────────────────────────────────────────────────────────────── */
const DEFAULT_LANDING_HTML = `<!DOCTYPE html>
<html lang="en" dir="auto">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <script src="https://cdn.tailwindcss.com"><\/script>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=Inter:wght@300;400;500;600&display=swap');

    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    html { scroll-behavior: smooth; }
    body { font-family: 'Inter', sans-serif; background: #07070d; color: #e8e7f4; overflow-x: hidden; }
    .font-display { font-family: 'Syne', sans-serif; }

    /* Gradient text */
    .g-text {
      background: linear-gradient(135deg, #f0eff8 0%, #7c6dfa 48%, #e8b84b 100%);
      -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
    }
    .g-text-gold {
      background: linear-gradient(135deg, #f0ca74 0%, #e8b84b 60%, #c47a2a 100%);
      -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
    }

    /* Pill */
    .pill {
      display: inline-flex; align-items: center; gap: 6px;
      padding: 5px 14px; border-radius: 999px;
      font-size: 11px; font-weight: 600; letter-spacing: .08em; text-transform: uppercase;
      border: 1px solid rgba(124,109,250,.3); color: #9d90fb;
      background: rgba(124,109,250,.08);
    }

    /* Glass card */
    .card {
      background: rgba(23,23,36,.7);
      backdrop-filter: blur(12px);
      border: 1px solid rgba(255,255,255,.07);
      border-radius: 18px;
      padding: 28px 24px;
      transition: border-color .25s, transform .25s, box-shadow .25s;
    }
    .card:hover {
      border-color: rgba(124,109,250,.38);
      transform: translateY(-3px);
      box-shadow: 0 12px 40px rgba(124,109,250,.13);
    }

    /* Icon chip */
    .icon-chip {
      width: 46px; height: 46px; border-radius: 14px;
      display: flex; align-items: center; justify-content: center;
      margin-bottom: 18px;
    }

    /* Step connector */
    .step-num {
      width: 34px; height: 34px; border-radius: 50%; flex-shrink: 0;
      display: flex; align-items: center; justify-content: center;
      font-size: 13px; font-weight: 700;
      background: linear-gradient(135deg,#7c6dfa,#5b4de0); color: #fff;
      box-shadow: 0 0 16px rgba(124,109,250,.4);
    }
    .connector { width: 1px; height: 44px; background: rgba(124,109,250,.18); margin: 4px auto; }

    /* Badge */
    .badge {
      display: inline-flex; align-items: center;
      padding: 6px 16px; border-radius: 999px; font-size: 12px; font-weight: 500;
    }

    /* Mesh background */
    .mesh {
      background:
        radial-gradient(ellipse 90% 70% at 15%  5%,  rgba(124,109,250,.12) 0%, transparent 55%),
        radial-gradient(ellipse 60% 50% at 85% 90%,  rgba(232,184, 75,.08) 0%, transparent 55%),
        radial-gradient(ellipse 50% 40% at 50% 50%,  rgba(52, 211,153,.03) 0%, transparent 60%),
        #07070d;
    }

    /* Glow ring behind SVG */
    .hero-glow {
      position: absolute;
      inset: -20%;
      background: radial-gradient(ellipse 70% 60% at 50% 50%, rgba(124,109,250,.14) 0%, transparent 70%);
      pointer-events: none;
    }

    /* Nav */
    nav {
      position: sticky; top: 0; z-index: 50;
      background: rgba(7,7,13,.85);
      backdrop-filter: blur(16px) saturate(1.4);
      border-bottom: 1px solid rgba(255,255,255,.05);
    }
  </style>
</head>
<body class="mesh">

  <!-- ── NAV ── -->
  <nav>
    <div style="max-width:1100px;margin:0 auto;padding:14px 28px;display:flex;align-items:center;justify-content:space-between;">
      <!-- Logo -->
      <div style="display:flex;align-items:center;gap:10px;">
        <!-- Abstract monogram SVG -->
        <svg width="34" height="34" viewBox="0 0 34 34" fill="none" xmlns="http://www.w3.org/2000/svg" style="border-radius:10px;">
          <defs>
            <linearGradient id="ng" x1="0" y1="0" x2="34" y2="34" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stop-color="#7c6dfa"/>
              <stop offset="100%" stop-color="#5b4de0"/>
            </linearGradient>
          </defs>
          <rect width="34" height="34" rx="10" fill="url(#ng)"/>
          <!-- Abstract B mark: two offset arcs -->
          <path d="M10 8 L10 26" stroke="rgba(255,255,255,.9)" stroke-width="2.2" stroke-linecap="round"/>
          <path d="M10 8 C10 8 20 8 20 13 C20 18 10 18 10 18" stroke="rgba(255,255,255,.9)" stroke-width="2" stroke-linecap="round" fill="none"/>
          <path d="M10 18 C10 18 22 18 22 22 C22 26 10 26 10 26" stroke="rgba(255,255,255,.75)" stroke-width="2" stroke-linecap="round" fill="none"/>
        </svg>
        <div>
          <div style="font-family:'Syne',sans-serif;font-size:15px;font-weight:700;color:#f0eff8;letter-spacing:.01em;line-height:1.2;">Branding AI</div>
          <div style="font-size:10px;color:#4c4c68;letter-spacing:.04em;text-transform:uppercase;">Strategy · Identity</div>
        </div>
      </div>
      <!-- Badge -->
      <span class="badge" style="background:rgba(232,184,75,.08);border:1px solid rgba(232,184,75,.25);color:#e8b84b;">✦ Beta</span>
    </div>
  </nav>

  <!-- ── HERO ── -->
  <section style="position:relative;overflow:hidden;padding:96px 28px 72px;text-align:center;">

    <!-- Abstract geometric SVG — Islamic-inspired interlocking rings & arcs -->
    <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:600px;height:400px;pointer-events:none;opacity:.18;z-index:0;">
      <svg width="600" height="400" viewBox="0 0 600 400" fill="none" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="hg1" x1="0" y1="0" x2="600" y2="400" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stop-color="#7c6dfa"/>
            <stop offset="100%" stop-color="#e8b84b"/>
          </linearGradient>
          <linearGradient id="hg2" x1="600" y1="0" x2="0" y2="400" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stop-color="#34d399" stop-opacity=".6"/>
            <stop offset="100%" stop-color="#7c6dfa" stop-opacity=".3"/>
          </linearGradient>
        </defs>
        <!-- Outer interlocking rings -->
        <circle cx="300" cy="200" r="160" stroke="url(#hg1)" stroke-width="1.2" fill="none"/>
        <circle cx="300" cy="200" r="120" stroke="url(#hg1)" stroke-width=".8" fill="none"/>
        <circle cx="300" cy="200" r="80"  stroke="url(#hg2)" stroke-width=".8" fill="none"/>
        <!-- Eight-fold symmetry lines -->
        <line x1="300" y1="40"  x2="300" y2="360" stroke="url(#hg1)" stroke-width=".6" opacity=".6"/>
        <line x1="140" y1="200" x2="460" y2="200" stroke="url(#hg1)" stroke-width=".6" opacity=".6"/>
        <line x1="187" y1="87"  x2="413" y2="313" stroke="url(#hg1)" stroke-width=".5" opacity=".5"/>
        <line x1="413" y1="87"  x2="187" y2="313" stroke="url(#hg1)" stroke-width=".5" opacity=".5"/>
        <!-- Arabesque arcs -->
        <path d="M 300 40 A 160 160 0 0 1 460 200" stroke="#7c6dfa" stroke-width="1.5" fill="none" opacity=".7"/>
        <path d="M 460 200 A 160 160 0 0 1 300 360" stroke="#e8b84b" stroke-width="1.5" fill="none" opacity=".5"/>
        <path d="M 300 360 A 160 160 0 0 1 140 200" stroke="#34d399" stroke-width="1.5" fill="none" opacity=".5"/>
        <path d="M 140 200 A 160 160 0 0 1 300 40"  stroke="#7c6dfa" stroke-width="1.5" fill="none" opacity=".5"/>
        <!-- Inner star points -->
        <polygon points="300,120 316,168 368,168 326,196 342,244 300,216 258,244 274,196 232,168 284,168"
          stroke="#7c6dfa" stroke-width=".8" fill="none" opacity=".5"/>
        <!-- Small accent dots -->
        <circle cx="300" cy="40"  r="4" fill="#7c6dfa" opacity=".8"/>
        <circle cx="460" cy="200" r="4" fill="#e8b84b" opacity=".8"/>
        <circle cx="300" cy="360" r="4" fill="#34d399" opacity=".8"/>
        <circle cx="140" cy="200" r="4" fill="#7c6dfa" opacity=".8"/>
      </svg>
    </div>

    <div style="max-width:760px;margin:0 auto;position:relative;z-index:1;">
      <div class="pill" style="margin-bottom:28px;">
        <svg width="7" height="7" viewBox="0 0 7 7"><circle cx="3.5" cy="3.5" r="3.5" fill="#7c6dfa"/></svg>
        AI-Powered Brand Studio
      </div>

      <h1 class="font-display g-text" style="font-size:clamp(2.5rem,6vw,4.2rem);font-weight:800;line-height:1.08;letter-spacing:-.02em;margin-bottom:24px;">
        Build a Brand<br/>Worth Believing In
      </h1>

      <p style="font-size:1.05rem;line-height:1.8;color:#7c7a99;max-width:520px;margin:0 auto 40px;">
        Describe your business in the chat. Get a complete landing page,
        brand identity, visual assets, and marketing strategy — generated live by AI.
      </p>

      <!-- Capability badges -->
      <div style="display:flex;flex-wrap:wrap;gap:10px;justify-content:center;">
        <span class="badge" style="background:rgba(124,109,250,.1);border:1px solid rgba(124,109,250,.22);color:#a89cf9;">Strategy &amp; Positioning</span>
        <span class="badge" style="background:rgba(232,184,76,.07);border:1px solid rgba(232,184,76,.2);color:#e8b84b;">Visual Identity</span>
        <span class="badge" style="background:rgba(124,109,250,.1);border:1px solid rgba(124,109,250,.22);color:#a89cf9;">Landing Page Generation</span>
        <span class="badge" style="background:rgba(52,211,153,.07);border:1px solid rgba(52,211,153,.2);color:#34d399;">Ethical by Design</span>
        <span class="badge" style="background:rgba(251,191,36,.07);border:1px solid rgba(251,191,36,.18);color:#fbbf24;">Multilingual · RTL</span>
      </div>
    </div>
  </section>

  <!-- ── HOW IT WORKS ── -->
  <section style="padding:60px 28px;max-width:560px;margin:0 auto;">
    <p style="text-align:center;font-size:11px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:#7c6dfa;margin-bottom:44px;">How it works</p>

    <div style="display:flex;flex-direction:column;align-items:flex-start;gap:0;">

      <!-- Step 1 -->
      <div style="display:flex;align-items:flex-start;gap:20px;width:100%;">
        <div style="display:flex;flex-direction:column;align-items:center;">
          <div class="step-num">1</div>
          <div class="connector"></div>
        </div>
        <div style="padding-bottom:36px;">
          <p class="font-display" style="font-size:.95rem;font-weight:700;color:#f0eff8;margin-bottom:6px;">Describe Your Business</p>
          <p style="font-size:.85rem;line-height:1.7;color:#7c7a99;">Type a short description of your brand, audience, and goals into the chat panel.</p>
        </div>
      </div>

      <!-- Step 2 -->
      <div style="display:flex;align-items:flex-start;gap:20px;width:100%;">
        <div style="display:flex;flex-direction:column;align-items:center;">
          <div class="step-num">2</div>
          <div class="connector"></div>
        </div>
        <div style="padding-bottom:36px;">
          <p class="font-display" style="font-size:.95rem;font-weight:700;color:#f0eff8;margin-bottom:6px;">Generate a Landing Page</p>
          <p style="font-size:.85rem;line-height:1.7;color:#7c7a99;">Hit <strong style="color:#a89cf9;">Generate Site →</strong> and watch a fully-coded landing page appear in seconds.</p>
        </div>
      </div>

      <!-- Step 3 -->
      <div style="display:flex;align-items:flex-start;gap:20px;width:100%;">
        <div style="display:flex;flex-direction:column;align-items:center;">
          <div class="step-num">3</div>
        </div>
        <div>
          <p class="font-display" style="font-size:.95rem;font-weight:700;color:#f0eff8;margin-bottom:6px;">Refine with the Strategy Director</p>
          <p style="font-size:.85rem;line-height:1.7;color:#7c7a99;">Ask the AI for logos, colour palettes, taglines, campaigns, or any brand asset — in any language.</p>
        </div>
      </div>

    </div>
  </section>

  <!-- ── FEATURES ── -->
  <section style="padding:20px 28px 80px;">
    <div style="max-width:1000px;margin:0 auto;display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:18px;">

      <!-- Feature: Landing Page Builder -->
      <div class="card">
        <div class="icon-chip" style="background:rgba(124,109,250,.12);border:1px solid rgba(124,109,250,.2);">
          <!-- Abstract grid SVG icon -->
          <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
            <rect x="2" y="2" width="8" height="8" rx="2" stroke="#7c6dfa" stroke-width="1.5"/>
            <rect x="12" y="2" width="8" height="8" rx="2" stroke="#7c6dfa" stroke-width="1.5" opacity=".6"/>
            <rect x="2" y="12" width="8" height="8" rx="2" stroke="#7c6dfa" stroke-width="1.5" opacity=".6"/>
            <rect x="12" y="12" width="8" height="8" rx="2" stroke="#7c6dfa" stroke-width="1.5" opacity=".4"/>
          </svg>
        </div>
        <p class="font-display" style="font-size:.9rem;font-weight:700;color:#f0eff8;margin-bottom:8px;">Landing Page Builder</p>
        <p style="font-size:.82rem;line-height:1.7;color:#7c7a99;">Full HTML pages generated from a single sentence — hero, features, CTA and all.</p>
      </div>

      <!-- Feature: Visual Identity -->
      <div class="card">
        <div class="icon-chip" style="background:rgba(232,184,75,.08);border:1px solid rgba(232,184,75,.18);">
          <!-- Abstract diamond/palette SVG icon -->
          <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
            <circle cx="11" cy="11" r="7" stroke="#e8b84b" stroke-width="1.5" fill="none"/>
            <circle cx="11" cy="11" r="3" stroke="#e8b84b" stroke-width="1.2" fill="none" opacity=".6"/>
            <line x1="11" y1="4" x2="11" y2="18" stroke="#e8b84b" stroke-width=".8" opacity=".4"/>
            <line x1="4" y1="11" x2="18" y2="11" stroke="#e8b84b" stroke-width=".8" opacity=".4"/>
          </svg>
        </div>
        <p class="font-display" style="font-size:.9rem;font-weight:700;color:#f0eff8;margin-bottom:8px;">Visual Identity</p>
        <p style="font-size:.82rem;line-height:1.7;color:#7c7a99;">Logo concepts, colour systems, and typography pairings crafted for your brand.</p>
      </div>

      <!-- Feature: Marketing Strategy -->
      <div class="card">
        <div class="icon-chip" style="background:rgba(52,211,153,.07);border:1px solid rgba(52,211,153,.18);">
          <!-- Abstract signal/wave SVG icon -->
          <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
            <path d="M2 16 C4 12 7 8 11 8 C15 8 18 12 20 16" stroke="#34d399" stroke-width="1.5" fill="none" stroke-linecap="round"/>
            <path d="M5 16 C7 13 9 10 11 10 C13 10 15 13 17 16" stroke="#34d399" stroke-width="1.2" fill="none" stroke-linecap="round" opacity=".6"/>
            <circle cx="11" cy="16" r="1.5" fill="#34d399"/>
          </svg>
        </div>
        <p class="font-display" style="font-size:.9rem;font-weight:700;color:#f0eff8;margin-bottom:8px;">Marketing Strategy</p>
        <p style="font-size:.82rem;line-height:1.7;color:#7c7a99;">Campaign ideas, social copy, brand voice guidelines, and go-to-market plans.</p>
      </div>

      <!-- Feature: Ethical by Default -->
      <div class="card">
        <div class="icon-chip" style="background:rgba(251,191,36,.07);border:1px solid rgba(251,191,36,.18);">
          <!-- Abstract star/compass SVG icon -->
          <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
            <polygon points="11,2 13.5,8.5 20.5,9 15.5,13.5 17.5,20.5 11,17 4.5,20.5 6.5,13.5 1.5,9 8.5,8.5"
              stroke="#fbbf24" stroke-width="1.3" fill="none" stroke-linejoin="round"/>
          </svg>
        </div>
        <p class="font-display" style="font-size:.9rem;font-weight:700;color:#f0eff8;margin-bottom:8px;">Ethical by Default</p>
        <p style="font-size:.82rem;line-height:1.7;color:#7c7a99;">Every output is honest, tasteful, and community-centred — no dark patterns.</p>
      </div>

    </div>
  </section>

  <!-- ── FOOTER ── -->
  <footer style="border-top:1px solid rgba(255,255,255,.05);padding:28px;text-align:center;">
    <!-- Abstract mini decorative SVG -->
    <svg width="40" height="2" viewBox="0 0 40 2" style="display:block;margin:0 auto 14px;">
      <line x1="0" y1="1" x2="16" y2="1" stroke="rgba(124,109,250,.3)" stroke-width="1.5"/>
      <circle cx="20" cy="1" r="2" fill="#7c6dfa" opacity=".6"/>
      <line x1="24" y1="1" x2="40" y2="1" stroke="rgba(232,184,75,.3)" stroke-width="1.5"/>
    </svg>
    <p style="font-size:11px;color:#4c4c68;">← Describe your business in the chat panel to get started</p>
  </footer>

</body>
</html>`;

export default function Home() {
  const [businessDescription, setBusinessDescription] = useState("");
  const [businessContext, setBusinessContext] = useState("");
  const [canvasHtml, setCanvasHtml] = useState<string>(DEFAULT_LANDING_HTML);
  const [canvasTitle, setCanvasTitle] = useState("Welcome");
  const [generatingSite, setGeneratingSite] = useState(false);
  const [siteGenerated, setSiteGenerated] = useState(false);

  const handleGenerateSite = async () => {
    if (!businessDescription.trim()) return;
    setGeneratingSite(true);
    try {
      const res = await fetch("/api/backend/api/generate-site", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ business_description: businessDescription }),
      });
      if (!res.ok) throw new Error(`Error ${res.status}`);
      const data: { html: string } = await res.json();
      setCanvasHtml(data.html);
      setCanvasTitle("Generated Landing Page");
      setBusinessContext(businessDescription);
      setSiteGenerated(true);
    } catch (err) {
      alert(`Failed to generate site: ${err instanceof Error ? err.message : err}`);
    } finally {
      setGeneratingSite(false);
    }
  };

  const handleArtifactGenerated = (html: string) => {
    setCanvasHtml(html);
    setCanvasTitle("Latest Visual Artifact");
  };

  return (
    <div className="flex flex-col h-screen overflow-hidden mesh-bg font-sans">

      {/* ── Header ── */}
      <header className="flex items-center justify-between px-6 py-3 glass shrink-0 z-10">
        <div className="flex items-center gap-3">
          {/* Abstract SVG logo mark */}
          <div className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0 glow-accent"
            style={{ background: "linear-gradient(135deg, #7c6dfa, #5b4de0)" }}>
            <svg width="18" height="18" viewBox="0 0 34 34" fill="none">
              <path d="M8 7 L8 27" stroke="rgba(255,255,255,.9)" strokeWidth="2.5" strokeLinecap="round"/>
              <path d="M8 7 C8 7 20 7 20 13 C20 19 8 19 8 19" stroke="rgba(255,255,255,.9)" strokeWidth="2.2" strokeLinecap="round" fill="none"/>
              <path d="M8 19 C8 19 22 19 22 23 C22 27 8 27 8 27" stroke="rgba(255,255,255,.75)" strokeWidth="2.2" strokeLinecap="round" fill="none"/>
            </svg>
          </div>
          <div className="flex flex-col leading-none gap-0.5">
            <span className="font-display text-sm font-bold tracking-tight" style={{ color: "var(--text-primary)" }}>
              Branding AI
            </span>
            <span className="text-[10px] tracking-widest uppercase" style={{ color: "var(--text-muted)" }}>
              Strategy · Identity · Excellence
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {siteGenerated && (
            <span
              className="text-xs font-medium px-3 py-1.5 rounded-full flex items-center gap-2"
              style={{
                background: "var(--emerald-muted)",
                border: "1px solid var(--emerald-border)",
                color: "var(--emerald)",
              }}
            >
              <span className="dot-live" />
              Site Generated
            </span>
          )}
          <div
            className="text-xs px-3 py-1.5 rounded-full font-semibold tracking-wide"
            style={{
              background: "var(--gold-muted)",
              border: "1px solid var(--gold-border)",
              color: "var(--gold)",
            }}
          >
            ✦ Beta
          </div>
        </div>
      </header>

      {/* ── Site Generation Bar ── */}
      <div
        className="shrink-0 px-6 py-3 z-10"
        style={{ borderBottom: "1px solid var(--bg-border)", background: "var(--bg-surface)" }}
      >
        <div className="flex gap-2.5 max-w-4xl">
          <div className="flex-1 relative">
            {/* Spark icon */}
            <div
              className="absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none"
              style={{ color: "var(--accent)" }}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                <path d="M13 2L4.09 12.26A1 1 0 0 0 5 14h6v8l8.91-10.26A1 1 0 0 0 19 10h-6V2z"
                  stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <input
              type="text"
              value={businessDescription}
              onChange={(e) => setBusinessDescription(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleGenerateSite()}
              placeholder="Describe your business to generate a landing page… (e.g. 'An organic skincare brand for modern Muslim women')"
              className="studio-input w-full rounded-xl pl-10 pr-4 py-2.5 text-sm"
              style={{
                background: "var(--bg-elevated)",
                border: "1px solid var(--bg-border)",
                color: "var(--text-primary)",
              }}
            />
          </div>
          <button
            onClick={handleGenerateSite}
            disabled={generatingSite || !businessDescription.trim()}
            className="px-5 py-2.5 rounded-xl text-sm font-semibold transition-all whitespace-nowrap"
            style={{
              background:
                generatingSite || !businessDescription.trim()
                  ? "var(--bg-elevated)"
                  : "linear-gradient(135deg, #7c6dfa, #5b4de0)",
              color:
                generatingSite || !businessDescription.trim()
                  ? "var(--text-muted)"
                  : "#fff",
              border: "1px solid transparent",
              cursor:
                generatingSite || !businessDescription.trim() ? "not-allowed" : "pointer",
              boxShadow:
                generatingSite || !businessDescription.trim()
                  ? "none"
                  : "0 0 20px rgba(124,109,250,0.35), 0 4px 12px rgba(0,0,0,0.3)",
            }}
          >
            {generatingSite ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin w-3.5 h-3.5" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
                Generating…
              </span>
            ) : (
              <span className="flex items-center gap-1.5">
                Generate Site
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                  <path d="M5 12h14M12 5l7 7-7 7" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </span>
            )}
          </button>
        </div>
      </div>

      {/* ── Main split-screen ── */}
      <div className="flex flex-1 overflow-hidden">

        {/* Left: Canvas */}
        <div
          className="flex-1 flex flex-col p-4 overflow-hidden"
          style={{ background: "var(--bg-base)" }}
        >
          <ArtifactRenderer codeString={canvasHtml} title={canvasTitle} />
        </div>

        {/* Divider */}
        <div className="w-px shrink-0" style={{ background: "var(--bg-border)" }} />

        {/* Right: Chat */}
        <div
          className="w-[380px] xl:w-[430px] shrink-0 flex flex-col overflow-hidden"
          style={{ background: "var(--bg-surface)" }}
        >
          {/* Chat header */}
          <div
            className="px-4 py-3 shrink-0 flex items-center gap-2.5"
            style={{ borderBottom: "1px solid var(--bg-border)" }}
          >
            {/* Animated live dot */}
            <span className="dot-live" />
            <h2
              className="font-display text-xs font-semibold tracking-widest uppercase"
              style={{ color: "var(--text-secondary)" }}
            >
              Strategy Director
            </h2>
            <span
              className="ml-auto text-[10px] px-2.5 py-1 rounded-full font-medium"
              style={{
                background: "rgba(124,109,250,0.08)",
                border: "1px solid rgba(124,109,250,0.18)",
                color: "var(--accent)",
              }}
            >
              AI · Live
            </span>
          </div>

          <div className="flex-1 overflow-hidden">
            <StrategyChat
              businessContext={businessContext}
              onArtifactGenerated={handleArtifactGenerated}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
