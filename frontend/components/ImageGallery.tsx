"use client";

/**
 * ImageGallery.tsx
 * ================
 * Displays the 3 generated logos and 9 social media post images.
 * Prompts are intentionally NOT shown to the user.
 */

import { useState, useCallback } from "react";

// ─── Types ────────────────────────────────────────────────────────────────────

interface ImageItem {
  url:   string;
  index: number;
}

interface ImageGalleryProps {
  jobId:          string;
  logoImages:     ImageItem[];
  postImages:     ImageItem[];
  brandName:      string;
  primaryColor?:  string;
  /** Base URL of the FastAPI backend (default: empty string = same origin) */
  apiBase?:       string;
}

// ─── Helper: download a single image ─────────────────────────────────────────

async function downloadImage(url: string, filename: string): Promise<void> {
  const res  = await fetch(url);
  const blob = await res.blob();
  const a    = document.createElement("a");
  a.href     = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  URL.revokeObjectURL(a.href);
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function Skeleton({ className }: { className?: string }) {
  return (
    <div
      className={`animate-pulse bg-gray-100 rounded-xl ${className ?? ""}`}
      aria-hidden="true"
    />
  );
}

// ─── Lightbox ────────────────────────────────────────────────────────────────

function Lightbox({
  src,
  alt,
  onClose,
}: {
  src:     string;
  alt:     string;
  onClose: () => void;
}) {
  return (
    // eslint-disable-next-line jsx-a11y/click-events-have-key-events
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label="Image preview"
    >
      {/* eslint-disable-next-line jsx-a11y/no-noninteractive-element-interactions */}
      <img
        src={src}
        alt={alt}
        onClick={(e) => e.stopPropagation()}
        className="max-w-[90vw] max-h-[90vh] rounded-2xl shadow-2xl border-2 border-white/20"
      />
      <button
        onClick={onClose}
        className="absolute top-5 right-5 text-white text-3xl font-bold hover:text-gray-300 transition-colors leading-none"
        aria-label="Close preview"
      >
        ×
      </button>
    </div>
  );
}

// ─── Single Image Card ────────────────────────────────────────────────────────

interface ImageCardProps {
  item:          ImageItem;
  label:         string;
  type:          "logo" | "post";
  jobId:         string;
  primaryColor:  string;
  apiBase:       string;
  onRegenerated: (index: number, newUrl: string) => void;
}

function ImageCard({
  item,
  label,
  type,
  jobId,
  primaryColor,
  apiBase,
  onRegenerated,
}: ImageCardProps) {
  const [lightbox,     setLightbox]     = useState(false);
  const [regenerating, setRegenerating] = useState(false);
  const [imgError,     setImgError]     = useState(false);
  const [error,        setError]        = useState("");
  const [currentUrl,   setCurrentUrl]   = useState(item.url);

  async function handleDownload() {
    const filename = `${type}_${item.index}.png`;
    await downloadImage(currentUrl, filename);
  }

  async function handleRegenerate() {
    setRegenerating(true);
    setError("");
    try {
      const res = await fetch(`${apiBase}/regenerate-image`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          job_id:      jobId,
          image_type:  type,
          image_index: item.index,
        }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data?.detail ?? `HTTP ${res.status}`);
      }
      const data = await res.json();
      // Prefix with proxy base so the static /exports path goes through /api/backend
      const rawUrl: string = data.image_url;
      const proxied = rawUrl.startsWith("/exports") ? `${apiBase}${rawUrl}` : rawUrl;
      // Append timestamp to bust browser cache
      const newUrl = `${proxied}?t=${Date.now()}`;
      setCurrentUrl(newUrl);
      setImgError(false);
      onRegenerated(item.index, newUrl);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Regeneration failed.");
    } finally {
      setRegenerating(false);
    }
  }

  return (
    <div className="group flex flex-col rounded-2xl border border-gray-200 bg-white shadow-sm hover:shadow-md transition-all duration-200 overflow-hidden">
      {/* Image area */}
      <div
        className="relative cursor-zoom-in aspect-square bg-gray-50 overflow-hidden"
        onClick={() => !imgError && setLightbox(true)}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === "Enter" && !imgError && setLightbox(true)}
        aria-label={`Preview ${label}`}
      >
        {imgError ? (
          /* Broken-image placeholder */
          <div className="w-full h-full flex flex-col items-center justify-center gap-2 bg-gray-50 text-gray-400 p-4 text-center">
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/>
              <polyline points="21 15 16 10 5 21"/>
            </svg>
            <span className="text-[11px] font-medium">Image unavailable</span>
            <span className="text-[10px] text-gray-300">Click Regenerate to retry</span>
          </div>
        ) : (
          <img
            src={currentUrl}
            alt={label}
            className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
            loading="lazy"
            onError={() => setImgError(true)}
          />
        )}
        {/* Hover overlay — only when image loaded */}
        {!imgError && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/0 group-hover:bg-black/25 transition-colors duration-200">
            <span className="opacity-0 group-hover:opacity-100 text-white text-sm font-medium bg-black/50 px-3 py-1.5 rounded-full transition-opacity duration-200">
              Preview
            </span>
          </div>
        )}
        {/* Index badge */}
        <span
          className="absolute top-2 left-2 text-white text-xs font-bold px-2 py-0.5 rounded-full"
          style={{ backgroundColor: primaryColor }}
        >
          {label}
        </span>
      </div>

      {/* Actions */}
      <div className="p-3 flex gap-2">
        <button
          onClick={handleDownload}
          className="flex-1 py-1.5 text-xs font-semibold rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 hover:border-gray-300 transition-colors"
        >
          ↓ Download
        </button>
        <button
          onClick={handleRegenerate}
          disabled={regenerating}
          className="flex-1 py-1.5 text-xs font-semibold rounded-lg text-white transition-colors disabled:opacity-60"
          style={{
            backgroundColor: regenerating ? "#9ca3af" : primaryColor,
          }}
        >
          {regenerating ? "⏳ …" : "↻ Regenerate"}
        </button>
      </div>

      {error && (
        <p className="px-3 pb-2 text-[11px] text-red-500">{error}</p>
      )}

      {lightbox && (
        <Lightbox
          src={currentUrl}
          alt={label}
          onClose={() => setLightbox(false)}
        />
      )}
    </div>
  );
}

// ─── Loading skeleton grid ────────────────────────────────────────────────────

function GallerySkeletons({ count }: { count: number }) {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="flex flex-col gap-2">
          <Skeleton className="aspect-square w-full" />
          <Skeleton className="h-8 w-full" />
        </div>
      ))}
    </>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

export default function ImageGallery({
  jobId,
  logoImages,
  postImages,
  brandName,
  primaryColor = "#3b5bdb",
  apiBase      = "",
}: ImageGalleryProps) {
  type Tab = "logos" | "posts";
  const [activeTab, setActiveTab] = useState<Tab>("logos");
  const [logos,     setLogos]     = useState<ImageItem[]>(logoImages);
  const [posts,     setPosts]     = useState<ImageItem[]>(postImages);

  const handleLogoRegenerated = useCallback((index: number, newUrl: string) => {
    setLogos((prev) =>
      prev.map((img) => (img.index === index ? { ...img, url: newUrl } : img))
    );
  }, []);

  const handlePostRegenerated = useCallback((index: number, newUrl: string) => {
    setPosts((prev) =>
      prev.map((img) => (img.index === index ? { ...img, url: newUrl } : img))
    );
  }, []);

  const tabs: { id: Tab; label: string; count: number }[] = [
    { id: "logos", label: "Logos",        count: logos.length },
    { id: "posts", label: "Social Posts", count: posts.length },
  ];

  const isLoadingLogos = logos.length === 0;
  const isLoadingPosts = posts.length === 0;

  return (
    <div className="w-full">
      {/* Tab bar */}
      <div className="flex gap-1 p-1 bg-gray-100 rounded-xl mb-6 w-fit">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-5 py-2 text-sm font-semibold rounded-lg transition-all duration-150 ${
              activeTab === tab.id
                ? "bg-white shadow-sm text-gray-900"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            {tab.label}
            <span
              className={`ml-2 text-xs px-1.5 py-0.5 rounded-full font-bold ${
                activeTab === tab.id ? "text-white" : "text-gray-400"
              }`}
              style={activeTab === tab.id ? { backgroundColor: primaryColor } : {}}
            >
              {tab.count}
            </span>
          </button>
        ))}
      </div>

      {/* ── Logos tab ── */}
      {activeTab === "logos" && (
        <div>
          <p className="text-sm text-gray-500 mb-4">
            3 logo variants generated for <strong>{brandName}</strong> using Islamic geometric design.
            These are brand identity marks — not product images. Click to preview full-size.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {isLoadingLogos ? (
              <GallerySkeletons count={3} />
            ) : (
              logos.map((img) => (
                <ImageCard
                  key={img.index}
                  item={img}
                  label={`Logo ${img.index}`}
                  type="logo"
                  jobId={jobId}
                  primaryColor={primaryColor}
                  apiBase={apiBase}
                  onRegenerated={handleLogoRegenerated}
                />
              ))
            )}
          </div>
        </div>
      )}

      {/* ── Posts tab ── */}
      {activeTab === "posts" && (
        <div>
          <p className="text-sm text-gray-500 mb-4">
            3 abstract brand visual concepts (1080×1080) — Islamic geometric art reflecting your brand identity.
            Use as background assets or visual inspiration on Instagram, Facebook, and LinkedIn.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {isLoadingPosts ? (
              <GallerySkeletons count={3} />
            ) : (
              posts.map((img) => (
                <ImageCard
                  key={img.index}
                  item={img}
                  label={`Visual ${img.index}`}
                  type="post"
                  jobId={jobId}
                  primaryColor={primaryColor}
                  apiBase={apiBase}
                  onRegenerated={handlePostRegenerated}
                />
              ))
            )}
          </div>
        </div>
      )}

      {/* Empty state */}
      {activeTab === "logos" && logos.length === 0 && (
        <div className="text-center py-16 text-gray-400">
          <p className="font-medium">No logos generated yet.</p>
          <p className="text-sm mt-1">
            Check that <code>HUGGINGFACE_API_TOKEN</code> is set in your backend .env file.
          </p>
        </div>
      )}
      {activeTab === "posts" && posts.length === 0 && (
        <div className="text-center py-16 text-gray-400">
          <p className="font-medium">No brand visuals generated yet.</p>
          <p className="text-sm mt-1">
            Check that <code>HUGGINGFACE_API_TOKEN</code> is set in your backend .env file.
          </p>
        </div>
      )}
    </div>
  );
}
