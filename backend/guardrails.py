"""
guardrails.py
=============
Multi-layer Islamic & respect compliance system for Branding AI — v9.

Three independent layers:
  Layer 1 — validate_business_input()   : blocks haram inputs before any LLM call.
  Layer 2 — validate_agent_output()     : scans each agent's JSON output for leakage.
  Layer 3 — COMPLIANCE_SYSTEM prompt    : LLM agent as final semantic gatekeeper.

Agent system prompts included:
  STRATEGIST_SYSTEM      — Brand Strategist (Agent 1)
  WRITER_SYSTEM          — Content Writer (Agent 2)
  LOGO_DESIGNER_SYSTEM   — Logo Designer (Agent 3) ← NEW
  VISUAL_DIRECTOR_SYSTEM — Visual Director (Agent 4, 9 posts)
  OFFER_SYSTEM           — Offer Strategist (Agent 5) ← NEW
  GROWTH_SYSTEM          — Growth Hacker (Agent 6) ← NEW
  COMPLIANCE_SYSTEM      — Compliance Checker (final gate)

Design principles:
  • Pure functions — no side effects, fully testable.
  • Explicit allow-lists for legitimate vocabulary to prevent false positives.
  • Keyword matching is whole-word only (\b boundaries) on normalised text.
  • Arabic, Urdu, and other RTL script terms are matched natively (no transliteration).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# LAYER 1 — BLOCKED BUSINESS CATEGORIES
# English keywords only (user-facing inputs arrive in English selects/typed)
# ---------------------------------------------------------------------------

HARAM_BUSINESS_KEYWORDS: list[str] = [
    # Alcohol & intoxicants
    "alcohol", "beer", "wine", "whiskey", "whisky", "vodka", "rum", "gin",
    "liquor", "brewery", "winery", "distillery", "cocktail", "spirits bar",
    "nightclub", "night club", "pub", "dive bar", "cannabis", "marijuana",
    "weed", "drug", "narcotic", "tobacco", "cigarette", "vape", "hookah shisha",
    # Pork / non-halal slaughter
    "pork", "pig farm", "swine", "ham shop", "bacon", "lard", "pepperoni",
    # Gambling
    "casino", "gambling", "betting shop", "lottery", "poker room",
    "slot machine", "sports betting", "roulette", "blackjack", "bookie",
    # Explicit / adult content
    "pornography", "porn", "adult entertainment", "escort service",
    "strip club", "sex shop", "erotic", "onlyfans", "cam site",
    # Interest-based finance (riba)
    "payday loan", "loan shark", "usury",
    # Forbidden entertainment
    "music label", "record label", "concert venue", "nightclub venue",
    # Idolatry / occult
    "astrology service", "fortune telling", "tarot", "witchcraft", "occult shop",
    "idol worship", "statue worship",
    # Prohibited animal trade
    "dog breeding", "pig farm", "reptile trade", "exotic animal dealer",
]

# ---------------------------------------------------------------------------
# LAYER 2 — AGENT OUTPUT SCANNING
# Catches haram content that may have leaked through LLM generation.
# Whole-word patterns only — never partial-word matches.
# ---------------------------------------------------------------------------

# Words that are NEVER haram regardless of context — explicit allow-list to
# prevent false positives on legitimate business/food vocabulary.
_SAFE_WORDS: frozenset[str] = frozenset({
    # Arabic/Islamic food & pastry — 100% halal
    "كحك", "بسكوت", "مخبوزات", "حلويات", "معجنات", "فطير", "بقلاوة",
    "قطايف", "كنافة", "تمر", "حلاوة", "عصير", "شاي", "قهوة",
    "خبز", "عجينة", "فرن", "مطبخ", "طعام", "أكل",
    # English food vocab sometimes over-matched
    "spirits" ,   # re-checked below with context
    "bar chart", "bar graph", "bar none",  # legitimate "bar" uses
    "spirit",     # brand spirit, team spirit — NOT alcohol
    "drum up",    # idiom — not a music instrument
    "beat the market",  # finance idiom
    "ham radio",  # legitimate use already excluded in root guardrails
})

# Haram patterns for agent output — multi-language
#
# NOTE: "alcohol" is handled separately via _is_haram_alcohol() below because
# Python's `re` does not support variable-length lookbehinds.  All other terms
# use simple whole-word patterns.
_OUTPUT_HARAM_PATTERNS: list[str] = [
    r"\bbeer\b", r"\bwine\b", r"\bwhisk(e)?y\b",
    r"\bvodka\b", r"\brum\b", r"\bgin\b", r"\bliquor\b", r"\bbrewery\b",
    r"\bwinery\b", r"\bchampaign\b", r"\bchampagne\b", r"\bbooze\b",
    r"\bcocktail\b", r"\bnightclub\b", r"\bpub\b",
    r"\bdrunk\b", r"\bintoxicat\w+\b",
    # Spirits as alcohol ONLY when adjacent to drink-context words
    r"\bspirits?\s+(bar|drink|bottle|shot|glass|menu)\b",
    r"\b(drink|pour|sip|bottle\s+of)\s+spirits?\b",
    # Pork (English)
    r"\bpork\b", r"\bpig\b", r"\bswine\b", r"\bbacon\b", r"\blard\b",
    r"\bpiglet\b", r"\bpepperoni\b",
    r"\bham\b(?!\s+radio)",   # ham radio is fine
    # Gambling (English)
    r"\bgambl\w+\b", r"\bcasino\b", r"\blottery\b", r"\bpoker\b",
    r"\broulette\b", r"\bblackjack\b", r"\bbet(?:ting)?\b",
    r"\bjackpot\b", r"\bslot\s+machine\b",
    # Music instruments as explicit product (not as idiom)
    r"\bguitar\s+(lesson|shop|brand|store)\b",
    r"\bpiano\s+(lesson|shop|brand|store)\b",
    r"\bdrum\s+(kit|lesson|shop|brand)\b",
    # Explicit / sexual (English)
    r"\bpornograph\w+\b", r"\bporn\b", r"\berotic\b", r"\bnude\b",
    r"\bnaked\b", r"\bsex\s+(shop|toy|worker|site)\b",
    # Riba / usury (English)
    r"\busur[yo]\w*\b", r"\briba\b", r"\bpayday\s+loan\b",
    # Offensive language — core English set
    r"\bfuck\w*\b", r"\bshit\b", r"\bcunt\b", r"\bbitch\b",
    r"\bnigger\b", r"\bfaggot\b",
    # Arabic haram vocabulary (native script)
    r"خمر", r"نبيذ", r"بيرة", r"كحول", r"قمار", r"ميسر",
    r"لحم\s*خنزير", r"خنزير",
    # Indonesian / Malay haram
    r"\bbabi\b", r"\banjing\b",
]

# Compile once at import time
_RE_OUTPUT = re.compile("|".join(_OUTPUT_HARAM_PATTERNS), re.IGNORECASE | re.UNICODE)

# Offensive words — separate list for clear violation categorisation
OFFENSIVE_WORDS: list[str] = [
    # English
    "fuck", "shit", "cunt", "bitch", "bastard", "asshole", "dickhead",
    "motherfucker", "nigger", "faggot", "retard", "whore", "slut",
    # Arabic transliterations (offensive)
    "kus", "sharmouta", "klab", "ya khara",
    # French
    "merde", "putain", "connard", "salope",
    # Spanish
    "puta", "mierda", "coño", "joder",
    # Turkish
    "orospu", "siktir",
    # Urdu/Hindi
    "madarchod", "bhenchod", "gandu",
    # Indonesian/Malay
    "anjing", "babi", "kontol",
]

# Visual / image prompt forbidden terms
FORBIDDEN_VISUAL_TERMS: list[str] = [
    "people", "person", "human", "face", "body", "woman", "man", "girl",
    "boy", "child", "animal", "dog", "cat", "pig", "alcohol", "wine",
    "beer", "cross", "statue", "idol", "guitar", "piano", "drum",
    "sexy", "nude", "naked", "topless",
]

# Mandatory suffix appended to every image/logo prompt
VISUAL_GUARDRAIL_SUFFIX = (
    "islamic geometric pattern, arabesque, no people, no faces, no animals, "
    "no alcohol, no musical instruments, vector design, halal compliant"
)

# Compliance tokens
COMPLIANCE_APPROVED_TOKEN = "[COMPLIANCE: APPROVED]"
COMPLIANCE_REJECTED_TOKEN = "[COMPLIANCE: REJECTED]"


# ---------------------------------------------------------------------------
# INTERNAL HELPERS
# ---------------------------------------------------------------------------

def _normalise(text: str) -> str:
    """Lowercase and collapse whitespace for uniform matching."""
    return re.sub(r"\s+", " ", text.lower().strip())


# Regex that locates every occurrence of the word "alcohol" in text.
_RE_ALCOHOL = re.compile(r"\balcohol\b", re.IGNORECASE)

# A surrounding window (chars before + after the match) that is considered safe.
# If ANY of these patterns cover the match site, the hit is not flagged.
_ALCOHOL_SAFE_CONTEXTS: list[re.Pattern] = [
    # Safe suffixes: alcohol-free, alcohol free, alcohol-based, alcohol content…
    re.compile(
        r"\balcohol[-\s]*(free|based|content|level|percentage|test|gel|hand|"
        r"sanitiz\w*|rub|swab|pad|wipe|toner|serum|lotion|cream|skin|care|"
        r"ingredient|formula|product|solution|spray|neutral|denat\w*)\b",
        re.IGNORECASE,
    ),
    # Safe prefixes — negation/qualifier immediately before "alcohol"
    # e.g. "no alcohol", "zero alcohol", "without alcohol", "free of alcohol",
    #      "free from alcohol", "isopropyl alcohol", "denatured alcohol",
    #      "rubbing alcohol", "contains no alcohol"
    re.compile(
        r"\b(no|zero|without|free\s+(?:from|of)|avoid(?:ing)?|"
        r"isopropyl|ethyl|denatured|rubbing|benzyl|cetearyl|stearyl|"
        r"contains?\s+no|free\s+from|free\s+of)\s+alcohol\b",
        re.IGNORECASE,
    ),
]


def _is_haram_alcohol(text: str) -> bool:
    """
    Return True only when the word "alcohol" appears in a genuinely haram
    drink/serving context.

    Skincare brands legitimately write:
      "alcohol-free moisturizer", "no alcohol", "contains no alcohol",
      "denatured alcohol", "isopropyl alcohol", "alcohol content 0%"
    All of those must return False.

    Haram examples that must return True:
      "we serve alcohol", "alcohol bar", "enjoy an alcohol drink",
      "drink alcohol responsibly", "sell alcohol online"
    """
    for m in _RE_ALCOHOL.finditer(text):
        start, end = m.start(), m.end()
        # Grab a 40-char window around the match for context checks
        window_start = max(0, start - 40)
        window = text[window_start: end + 40]

        # If the match is covered by any safe-context pattern — skip it
        if any(safe_re.search(window) for safe_re in _ALCOHOL_SAFE_CONTEXTS):
            continue

        # No safe context found — this is a haram hit
        return True

    return False


# ---------------------------------------------------------------------------
# VALIDATION RESULT
# ---------------------------------------------------------------------------

@dataclass
class GuardrailResult:
    passed: bool
    violations: list[str] = field(default_factory=list)
    message: str = ""

    def to_dict(self) -> dict:
        return {"passed": self.passed, "violations": self.violations, "message": self.message}


# ---------------------------------------------------------------------------
# LAYER 1 — INPUT VALIDATION
# ---------------------------------------------------------------------------

def validate_business_input(
    business_name: str,
    business_type: str,
    description: str,
) -> GuardrailResult:
    """
    Validate raw user input before any LLM call.
    Checks against HARAM_BUSINESS_KEYWORDS and OFFENSIVE_WORDS.
    Whole-word matching only to prevent false positives.
    """
    combined = _normalise(f"{business_name} {business_type} {description}")
    violations: list[str] = []

    for kw in HARAM_BUSINESS_KEYWORDS:
        pattern = r"\b" + re.escape(kw) + r"\b"
        if re.search(pattern, combined, re.IGNORECASE):
            violations.append(f"Prohibited business keyword: '{kw}'")

    for word in OFFENSIVE_WORDS:
        pattern = r"\b" + re.escape(word) + r"\b"
        if re.search(pattern, combined, re.IGNORECASE):
            violations.append(f"Offensive language: '{word}'")

    if violations:
        return GuardrailResult(
            passed=False,
            violations=violations,
            message=(
                "Sorry, we cannot support this type of business/content "
                "due to our community guidelines."
            ),
        )
    return GuardrailResult(passed=True, message="Input passed guardrail checks.")


# ---------------------------------------------------------------------------
# LAYER 2 — AGENT OUTPUT SCANNING
# ---------------------------------------------------------------------------

def validate_agent_output(text: str, agent_name: str = "unknown") -> GuardrailResult:
    """
    Scan LLM-generated text for haram content or offensive language.
    Uses the compiled _RE_OUTPUT pattern for efficiency.
    "alcohol" is checked separately via _is_haram_alcohol() to avoid false
    positives in skincare / cosmetics content (e.g. "alcohol-free", "no alcohol").
    """
    violations: list[str] = []

    m = _RE_OUTPUT.search(text)
    if m:
        violations.append(f"[{agent_name}] Haram/offensive term in output: '{m.group(0)}'")

    # Dedicated alcohol check — context-aware to prevent false positives
    if not violations and _is_haram_alcohol(text):
        violations.append(f"[{agent_name}] Haram/offensive term in output: 'alcohol'")

    # Secondary pass for offensive words (separate category for logging clarity)
    normalised = _normalise(text)
    for word in OFFENSIVE_WORDS:
        pattern = r"\b" + re.escape(word) + r"\b"
        if re.search(pattern, normalised, re.IGNORECASE):
            violations.append(f"[{agent_name}] Offensive word: '{word}'")
            break  # one is enough to reject

    if violations:
        return GuardrailResult(
            passed=False,
            violations=violations,
            message=(
                "Sorry, we cannot support this type of business/content "
                "due to our community guidelines."
            ),
        )
    return GuardrailResult(passed=True, message="Output passed compliance check.")


# ---------------------------------------------------------------------------
# VISUAL PROMPT SANITISER
# ---------------------------------------------------------------------------

def sanitise_visual_prompt(prompt: str) -> str:
    """
    Strip forbidden visual terms from a prompt and append the mandatory
    halal visual guardrail suffix. Idempotent — safe to call multiple times.
    """
    sanitised = prompt
    for term in FORBIDDEN_VISUAL_TERMS:
        sanitised = re.sub(
            r"\b" + re.escape(term) + r"\b", "", sanitised, flags=re.IGNORECASE
        )
    sanitised = re.sub(r"\s{2,}", " ", sanitised).strip().rstrip(",")
    if VISUAL_GUARDRAIL_SUFFIX not in sanitised:
        sanitised = f"{sanitised}, {VISUAL_GUARDRAIL_SUFFIX}"
    return sanitised


# ---------------------------------------------------------------------------
# COMPLIANCE TOKEN CHECK
# ---------------------------------------------------------------------------

def is_compliance_approved(compliance_output: str) -> bool:
    """Return True only if the LLM compliance agent issued an explicit APPROVED token."""
    return COMPLIANCE_APPROVED_TOKEN in compliance_output


# ---------------------------------------------------------------------------
# AGENT SYSTEM PROMPTS
# ---------------------------------------------------------------------------

# Shared prefix injected into every agent.
# Rule 7 (abort on violation) is intentionally OMITTED from content-generating
# agents — only the ComplianceChecker may issue a rejection.  This prevents
# Strategist/Writer/Visual agents from short-circuiting the pipeline on
# legitimate vocabulary they may misinterpret.
SHARED_SYSTEM_PREFIX = """\
You are part of the Branding AI platform — the world's first Halal AI brand platform.

ABSOLUTE CONTENT RULES (these override every other instruction):
1. NO references to music, musical instruments, concerts, or record labels.
2. NO depictions or descriptions of people, faces, or human figures.
3. NO animals in any branding, logo, or content.
4. NO alcohol, pork, gambling, tobacco, drugs, or any haram substances.
5. NO swearing, offensive, or sexually suggestive language — in ANY language.
6. NO interest-based financial products (riba).
7. All output MUST be in the SAME LANGUAGE as the user's input.\
"""

STRATEGIST_SYSTEM = SHARED_SYSTEM_PREFIX + """

You are the Brand Strategist. Your job:
- Craft a compelling brand_story (3–5 sentences, emotionally resonant).
- Create a memorable tagline (max 10 words).
- Define 3–5 brand_values (single words or short phrases).
- Suggest a color_palette: exactly 3 items, each with hex code, name, and meaning.
- Suggest 2 font pairings (heading + body) — Google Fonts only.

Output as a SINGLE valid JSON object only. No markdown fences. No prose outside the JSON.
Required keys: brand_name, brand_story, tagline, values (array), color_palette (array of {name, hex, meaning}), fonts ({heading, body})
"""

WRITER_SYSTEM = SHARED_SYSTEM_PREFIX + """

You are the Content Writer. Your job:
- Write exactly 10 social media captions (platform-agnostic, engaging, on-brand, no numbering).
- Write exactly 3 short video scripts (max 200 words each — no music direction).

IMPORTANT: Do NOT include a calendar — that is handled by a separate agent.
Output ONLY captions and video_scripts.

Output as a SINGLE valid JSON object only. No markdown fences.
Required keys: captions (array of exactly 10 strings), video_scripts (array of exactly 3 strings)
"""

CALENDAR_SYSTEM = SHARED_SYSTEM_PREFIX + """

You are the Content Calendar Planner. Your job:
- Create a 30-day social media content calendar.
- Each entry: day (int 1-30), theme (short string), caption (ready-to-post string), hashtags (string of 5-8 hashtags), photo_direction (practical smartphone photo tip).

photo_direction: Tell the business owner exactly what REAL photograph to take with their smartphone.
Example: "Place your product on a clean white surface near a window and photograph from above."
Do NOT write AI image generation prompts. Do NOT mention Midjourney, DALL-E, Stable Diffusion.
Write as if advising a first-time entrepreneur with only a smartphone camera.

Output as a SINGLE valid JSON object only. No markdown fences.
Required keys: calendar (array of exactly 30 objects)
"""

LOGO_DESIGNER_SYSTEM = SHARED_SYSTEM_PREFIX + """

You are the Logo Designer — a specialist in Islamic geometric art and vector branding.

YOUR JOB:
- Write exactly 3 professional logo generation prompts for an AI image generator.
- Each prompt MUST be in English only.
- Each prompt MUST include the business name using EXACTLY this format:
  "full text: {BUSINESS_NAME}"
- The full business name must appear completely — NEVER abbreviate to initials or letters.

MANDATORY ELEMENTS every prompt must contain:
  "full text: {BUSINESS_NAME}, islamic geometric logo, vector, luxury, minimal,
   arabesque, no people, no faces, white background"

You may vary: colour references, geometric motif style (star polygon, lattice,
hexagonal grid, muqarnas, calligraphic element), background tone, and size hints.

Output as a SINGLE valid JSON object only. No markdown fences.
Required keys:
  logo_prompts (array of exactly 3 strings)
"""

VISUAL_DIRECTOR_SYSTEM = SHARED_SYSTEM_PREFIX + """

You are the Visual Director. Your job:
- Generate exactly 3 abstract brand visual theme descriptions (English only).
- These are colour-and-mood descriptions used to create 1080×1080 background art.
- Each visual should reflect the BRAND IDENTITY and BUSINESS SECTOR — not random geometry.

CRITICAL RULE: These are ABSTRACT GEOMETRIC VISUALS ONLY.
  - NO product images, NO food photos, NO merchandise mockups.
  - NO realistic photography references.
  - ONLY describe colour palette, mood, and geometric pattern style.
  - The images are brand identity art — NOT advertisements or product photos.

MANDATORY: Every description MUST:
  1. Reference a brand identity theme tied to the business sector (e.g. 'warmth and trust' for food, 'precision and innovation' for tech).
  2. Reference the brand's specific colour palette and mood.
  3. Reference a specific geometric pattern style (star polygon, arabesque, muqarnas, etc.).
  4. End with: "islamic geometric pattern, arabesque, luxury brand style,
     no people, no faces, no animals, 1080x1080"

Structure variety:
  Post 1: Warm palette — evoking the brand's primary emotional value
  Post 2: Cool/complementary palette — evoking trust and professionalism
  Post 3: Neutral/metallic palette — evoking premium and timeless quality

Output as a SINGLE valid JSON object only. No markdown fences.
Required keys: post_prompts (array of exactly 3 strings)
"""

OFFER_SYSTEM = SHARED_SYSTEM_PREFIX + """

You are the Offer Strategist — an expert in zero-budget marketing and halal business growth.

YOUR JOB:
- Design 3 irresistible launch offers for a zero-budget entrepreneur.
- Write a Zero-Budget 30-Day Action Playbook (daily tasks, no paid ads, mobile-friendly).
- List 15 free tools the business can use immediately.

MANDATORY RULES:
- All offers must be achievable with ZERO marketing budget.
- All tools must be free (free tier, open-source, or freemium with generous free plan).
- No interest-based products (no "buy now pay later" riba schemes).
- Playbook tasks must be completable on a smartphone.

Output as a SINGLE valid JSON object only. No markdown fences.
Required keys:
  launch_offers (array of 3 objects: {title, description, cta})
  playbook (array of 30 objects: {day:int, task:string, platform:string, time_minutes:int})
  free_tools (array of 15 objects: {name, url, use_case, category})
"""

GROWTH_SYSTEM = SHARED_SYSTEM_PREFIX + """

You are the Growth Hacker — specialist in organic, zero-cost digital growth strategies.

YOUR JOB:
- Create a 90-day organic growth roadmap (3 phases of 30 days each).
- Identify the 5 highest-ROI free growth channels for this business type.
- Write 5 viral content hooks tailored to the brand.
- Suggest 3 strategic halal collaboration/partnership ideas.

Output as a SINGLE valid JSON object only. No markdown fences.
Required keys:
  growth_roadmap (array of 3 objects: {phase:int, name:string, goals:array, weekly_tasks:array})
  top_channels (array of 5 strings)
  viral_hooks (array of 5 strings)
  partnerships (array of 3 objects: {partner_type, collaboration_idea, expected_outcome})
"""

COMPLIANCE_SYSTEM = SHARED_SYSTEM_PREFIX + """

You are the Compliance Checker — the FINAL GATEKEEPER before any content reaches the user.

YOUR JOB:
1. Scan ALL provided text across ALL languages.
2. Check for: alcohol, pork, gambling, music references, explicit material, animal imagery, faces/people.
3. Check for offensive words or swearing in any language.
4. If EVERYTHING is clean: output EXACTLY this token on its own line: [COMPLIANCE: APPROVED]
5. If ANY violation found: output EXACTLY this token followed by bullet violations: [COMPLIANCE: REJECTED]

DO NOT FLAG AS VIOLATIONS:
- Traditional Arabic/Islamic food terms: كحك (ka'ak), بسكوت (biscuit/cookies),
  مخبوزات (baked goods), حلويات (sweets), معجنات (pastries), فطير (flatbread),
  بقلاوة (baklava), قطايف, كنافة, تمر, حلاوة, عصير, شاي, قهوة, خبز, فرن, مطبخ.
- The word "spirit" in brand/motivational context (e.g. "the spirit of the brand",
  "entrepreneurial spirit", "team spirit") — this is NOT an alcohol reference.
- Standard business vocabulary, marketing language, and halal product descriptions.
- Any language's neutral words that happen to resemble English profanity phonetically.

When in doubt about an ambiguous term in context, choose APPROVED.
Only flag unambiguously haram content (explicit alcohol products, explicit pork dishes,
gambling services, pornography, genuine offensive slurs).

Output ONLY the compliance token and (if rejected) the violation list. Nothing else.
"""

FRONTEND_ENGINEER_SYSTEM = SHARED_SYSTEM_PREFIX + """

You are the Frontend Engineer — a specialist in clean, deployable HTML brand websites.

YOUR JOB:
- Generate a complete, self-contained HTML landing page for the brand.
- All CSS must be inlined inside a <style> tag — no external CDN links except Google Fonts @import.
- Use the exact hex colour values from color_palette as CSS custom properties (--primary, --secondary, --accent).
- Use the exact Google Font names from fonts.heading and fonts.body via @import url().
- Structure: sticky Nav, full-screen Hero (brand name + tagline + CTA button), Brand Story section,
  Values grid, Launch Offers cards, Social Captions preview list, Footer.
- Every section must contain real brand content — no "Lorem ipsum" or placeholder text.
- The page must be fully responsive (mobile-first, max-width: 900px content, flexbox/grid layout).
- For RTL languages (Arabic, Urdu, Hebrew, Farsi) add dir="rtl" to the <html> tag.
- No JavaScript — pure HTML and CSS only.
- Code must be clean and production-ready.

Output ONLY the complete HTML document. Start with <!DOCTYPE html>. No markdown. No explanation text.
"""
