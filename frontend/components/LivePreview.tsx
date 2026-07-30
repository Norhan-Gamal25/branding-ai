"use client";

// components/LivePreview.tsx
// Renders AI-generated HTML/Tailwind inside an isolated iframe.
// Toggle between the live visual view and the raw source code.

import { useState } from "react";

interface LivePreviewProps {
  /** Raw HTML string returned by /api/generate-site */
  codeString: string;
}

/** Inject the Tailwind CDN script into the <head> of the HTML document. */
function injectTailwind(html: string): string {
  const tailwindTag = `<script src="https://cdn.tailwindcss.com"><\/script>`;
  // If the agent already included the CDN tag, don't double-inject
  if (html.includes("cdn.tailwindcss.com")) return html;
  return html.replace(/<\/head>/i, `  ${tailwindTag}\n</head>`);
}

export default function LivePreview({ codeString }: LivePreviewProps) {
  const [view, setView] = useState<"preview" | "code">("preview");

  const srcDoc = injectTailwind(codeString);

  return (
    <div className="flex flex-col w-full h-full rounded-xl border border-gray-200 overflow-hidden shadow-sm">
      {/* ── Toolbar ─────────────────────────────────────────────────── */}
      <div className="flex items-center gap-2 px-4 py-2 bg-gray-50 border-b border-gray-200">
        <span className="text-sm font-medium text-gray-500 mr-auto">
          Generated Landing Page
        </span>
        <button
          onClick={() => setView("preview")}
          className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
            view === "preview"
              ? "bg-indigo-600 text-white"
              : "bg-white text-gray-600 border border-gray-300 hover:bg-gray-100"
          }`}
        >
          Live Preview
        </button>
        <button
          onClick={() => setView("code")}
          className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
            view === "code"
              ? "bg-indigo-600 text-white"
              : "bg-white text-gray-600 border border-gray-300 hover:bg-gray-100"
          }`}
        >
          Raw Code
        </button>
        <button
          onClick={() => {
            const blob = new Blob([codeString], { type: "text/html" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = "landing-page.html";
            a.click();
            URL.revokeObjectURL(url);
          }}
          className="px-3 py-1 text-xs font-medium rounded-md bg-white text-gray-600 border border-gray-300 hover:bg-gray-100 transition-colors"
          title="Download HTML file"
        >
          ↓ Download
        </button>
      </div>

      {/* ── Content area ────────────────────────────────────────────── */}
      {view === "preview" ? (
        <iframe
          srcDoc={srcDoc}
          title="Generated Landing Page"
          sandbox="allow-scripts allow-same-origin"
          className="w-full flex-1"
          style={{ minHeight: "600px", border: "none" }}
        />
      ) : (
        <pre
          className="flex-1 overflow-auto bg-gray-900 text-green-300 text-xs p-4 font-mono leading-relaxed"
          style={{ minHeight: "600px" }}
        >
          <code>{codeString}</code>
        </pre>
      )}
    </div>
  );
}
