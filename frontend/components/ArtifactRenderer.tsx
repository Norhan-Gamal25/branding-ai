"use client";

import { useRef, useState } from "react";

interface ArtifactRendererProps {
  codeString: string;
  title?: string;
}

const TAILWIND_CDN = '<script src="https://cdn.tailwindcss.com"></' + "script>";

/**
 * Intercept script injected into every rendered page.
 * - Smooth-scrolls same-page anchors (#section)
 * - Opens external/path links in a new tab (_blank)
 * - Prevents any navigation that would hijack the parent window
 */
const INTERCEPT_SCRIPT = `
<script>
(function(){
  function handleClick(e){
    var el = e.target.closest('a[href]');
    if(!el) return;
    var href = el.getAttribute('href') || '';
    if(href.startsWith('#')){
      e.preventDefault();
      var target = document.querySelector(href);
      if(target) target.scrollIntoView({behavior:'smooth'});
      return;
    }
    e.preventDefault();
    window.open(href,'_blank','noopener,noreferrer');
  }
  document.addEventListener('click', handleClick, true);
})();
<\/script>`;

function buildSrcDoc(code: string): string {
  const hasHtml = /<html[\s\S]*?>/i.test(code);

  if (hasHtml) {
    let doc = code;
    if (!doc.includes("cdn.tailwindcss.com")) {
      doc = doc.replace(/<head([^>]*)>/i, `<head$1>\n  ${TAILWIND_CDN}`);
    }
    doc = doc.replace(/<\/body>/i, `${INTERCEPT_SCRIPT}\n</body>`);
    return doc;
  }

  return `<!DOCTYPE html>
<html lang="en" dir="auto">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  ${TAILWIND_CDN}
  <style>body { margin: 0; padding: 0; }</style>
</head>
<body>
${code}
${INTERCEPT_SCRIPT}
</body>
</html>`;
}

type DeviceMode = "desktop" | "tablet" | "mobile";

const DEVICE_WIDTHS: Record<DeviceMode, string> = {
  desktop: "100%",
  tablet:  "768px",
  mobile:  "375px",
};

/* ── Abstract SVG device icons ──────────────────────────────────────────────── */
function DesktopIcon({ active }: { active: boolean }) {
  const c = active ? "#fff" : "var(--text-muted)";
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <rect x="1" y="2" width="14" height="10" rx="1.5" stroke={c} strokeWidth="1.2" fill="none"/>
      <line x1="5" y1="14" x2="11" y2="14" stroke={c} strokeWidth="1.2" strokeLinecap="round"/>
      <line x1="8" y1="12" x2="8" y2="14" stroke={c} strokeWidth="1.2" strokeLinecap="round"/>
    </svg>
  );
}
function TabletIcon({ active }: { active: boolean }) {
  const c = active ? "#fff" : "var(--text-muted)";
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <rect x="3" y="1" width="10" height="14" rx="1.5" stroke={c} strokeWidth="1.2" fill="none"/>
      <circle cx="8" cy="13" r="0.8" fill={c}/>
    </svg>
  );
}
function MobileIcon({ active }: { active: boolean }) {
  const c = active ? "#fff" : "var(--text-muted)";
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <rect x="4.5" y="1" width="7" height="14" rx="1.5" stroke={c} strokeWidth="1.2" fill="none"/>
      <circle cx="8" cy="13" r="0.7" fill={c}/>
      <line x1="6.5" y1="3" x2="9.5" y2="3" stroke={c} strokeWidth="1.2" strokeLinecap="round"/>
    </svg>
  );
}

export default function ArtifactRenderer({
  codeString,
  title = "Visual Artifact",
}: ArtifactRendererProps) {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [copied, setCopied] = useState(false);
  const [device, setDevice] = useState<DeviceMode>("desktop");

  const srcDoc = buildSrcDoc(codeString);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(codeString);
    } catch {
      const el = document.createElement("textarea");
      el.value = codeString;
      document.body.appendChild(el);
      el.select();
      document.execCommand("copy");
      document.body.removeChild(el);
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([srcDoc], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${title.replace(/\s+/g, "-").toLowerCase()}.html`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleOpenNew = () => {
    const blob = new Blob([srcDoc], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    window.open(url, "_blank");
  };

  const deviceButtons: { id: DeviceMode; label: string }[] = [
    { id: "desktop", label: "Desktop" },
    { id: "tablet",  label: "Tablet"  },
    { id: "mobile",  label: "Mobile"  },
  ];

  return (
    <div
      className="flex flex-col h-full w-full rounded-2xl overflow-hidden"
      style={{ border: "1px solid var(--bg-border)", background: "var(--bg-surface)" }}
    >
      {/* ── Toolbar ── */}
      <div
        className="flex items-center justify-between px-4 py-2.5 shrink-0"
        style={{ borderBottom: "1px solid var(--bg-border)", background: "var(--bg-elevated)" }}
      >
        {/* Traffic lights + title */}
        <div className="flex items-center gap-2 min-w-0">
          <div className="flex gap-1.5 shrink-0">
            <div className="w-2.5 h-2.5 rounded-full" style={{ background: "#ff5f57" }} />
            <div className="w-2.5 h-2.5 rounded-full" style={{ background: "#febc2e" }} />
            <div className="w-2.5 h-2.5 rounded-full" style={{ background: "#28c840" }} />
          </div>
          {/* Abstract separator */}
          <div className="w-px h-4 mx-1" style={{ background: "var(--bg-border)" }} />
          <span
            className="font-display text-xs font-semibold tracking-wide uppercase truncate"
            style={{ color: "var(--text-secondary)" }}
          >
            {title}
          </span>
        </div>

        {/* Device switcher — abstract SVG icons */}
        <div
          className="hidden sm:flex items-center gap-0.5 px-1.5 py-1 rounded-lg"
          style={{ background: "var(--bg-surface)", border: "1px solid var(--bg-border)" }}
        >
          {deviceButtons.map(({ id, label }) => (
            <button
              key={id}
              onClick={() => setDevice(id)}
              title={label}
              className="px-2 py-1 rounded-md text-xs transition-all flex items-center justify-center"
              style={{
                background: device === id ? "var(--accent)" : "transparent",
                cursor: "pointer",
                boxShadow: device === id ? "0 0 8px var(--accent-glow)" : "none",
              }}
            >
              {id === "desktop" && <DesktopIcon active={device === id} />}
              {id === "tablet"  && <TabletIcon  active={device === id} />}
              {id === "mobile"  && <MobileIcon  active={device === id} />}
            </button>
          ))}
        </div>

        {/* Actions */}
        <div className="flex gap-1.5 shrink-0">
          <button
            onClick={handleCopy}
            className="text-xs px-3 py-1.5 rounded-lg font-medium transition-all flex items-center gap-1.5"
            style={{
              background: "var(--bg-surface)",
              border: `1px solid ${copied ? "rgba(52,211,153,0.3)" : "var(--bg-border)"}`,
              color: copied ? "var(--emerald)" : "var(--text-secondary)",
              cursor: "pointer",
            }}
          >
            {copied ? (
              <>
                {/* Abstract check mark SVG */}
                <svg width="11" height="11" viewBox="0 0 12 12" fill="none">
                  <path d="M2 6 L5 9 L10 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
                Copied
              </>
            ) : (
              <>
                {/* Abstract copy icon SVG */}
                <svg width="11" height="11" viewBox="0 0 12 12" fill="none">
                  <rect x="1" y="3" width="7" height="8" rx="1" stroke="currentColor" strokeWidth="1.2" fill="none"/>
                  <path d="M4 3 V2 a1 1 0 0 1 1-1 h5 a1 1 0 0 1 1 1 v7 a1 1 0 0 1-1 1 h-1" stroke="currentColor" strokeWidth="1.2" fill="none" strokeLinecap="round"/>
                </svg>
                Copy
              </>
            )}
          </button>
          <button
            onClick={handleOpenNew}
            className="text-xs px-3 py-1.5 rounded-lg font-medium transition-all flex items-center gap-1.5"
            style={{
              background: "var(--bg-surface)",
              border: "1px solid var(--bg-border)",
              color: "var(--text-secondary)",
              cursor: "pointer",
            }}
          >
            {/* Abstract external link SVG */}
            <svg width="11" height="11" viewBox="0 0 12 12" fill="none">
              <path d="M7 1 h4 v4" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M5 7 L11 1" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/>
              <path d="M5 2 H2 a1 1 0 0 0-1 1 v7 a1 1 0 0 0 1 1 h7 a1 1 0 0 0 1-1 v-3" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" fill="none"/>
            </svg>
            Open
          </button>
          <button
            onClick={handleDownload}
            className="text-xs px-3 py-1.5 rounded-lg font-medium transition-all flex items-center gap-1.5"
            style={{
              background: "linear-gradient(135deg, #7c6dfa, #5b4de0)",
              color: "#fff",
              cursor: "pointer",
              boxShadow: "0 0 14px rgba(124,109,250,0.35)",
              border: "1px solid transparent",
            }}
          >
            {/* Abstract download SVG */}
            <svg width="11" height="11" viewBox="0 0 12 12" fill="none">
              <path d="M6 1 v7 M3 6 l3 3 3-3" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M1 10 h10" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/>
            </svg>
            Download
          </button>
        </div>
      </div>

      {/* ── Canvas ── */}
      <div
        className="flex-1 flex items-start justify-center overflow-auto py-4"
        style={{ background: "#0e0e18" }}
      >
        <div
          className="transition-all duration-300 relative rounded-xl overflow-hidden"
          style={{
            width: DEVICE_WIDTHS[device],
            maxWidth: "100%",
            /* Desktop: fill the canvas; tablet/mobile: use device-accurate height */
            height: device === "desktop" ? "100%" : device === "tablet" ? "1024px" : "812px",
            /* Generated pages are often 2000–4000px tall — enforce a sensible minimum */
            minHeight: device === "desktop" ? "600px" : undefined,
            boxShadow:
              device !== "desktop"
                ? "0 0 0 1px var(--bg-border), 0 24px 64px rgba(0,0,0,0.6)"
                : "none",
          }}
        >
          {/*
            sandbox flags:
            - allow-scripts          : Tailwind CDN + any inline JS in the generated page
            - allow-same-origin      : needed for Tailwind to read/write document styles
            - allow-forms            : form elements in generated pages work
            - allow-popups           : window.open() calls inside the page work
            - allow-popups-to-escape-sandbox : links that open _blank escape the sandbox
            NO allow-top-navigation  : prevents the page from navigating the parent app
          */}
          <iframe
            ref={iframeRef}
            srcDoc={srcDoc}
            sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-popups-to-escape-sandbox"
            className="w-full border-0"
            title={title}
            style={{
              /* On desktop the canvas div is flex-1 so the iframe must fill it */
              height: "100%",
              /* Ensure tall generated pages are fully scrollable on desktop */
              minHeight: device === "desktop" ? "600px" : undefined,
              display: "block",
            }}
          />
        </div>
      </div>
    </div>
  );
}
