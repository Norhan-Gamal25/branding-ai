// app/api/backend/[...path]/route.ts
// Runtime reverse-proxy — reads BACKEND_URL at request time, not build time.
// This replaces the next.config.js rewrite so the target URL is not frozen
// into the standalone build artifact.
//
// Static image files (/exports/…) are redirected directly to the backend
// so large PNGs bypass Vercel's 10 MB serverless response limit and
// the browser fetches them straight from the origin (Render).

import { NextRequest, NextResponse } from "next/server";

const BACKEND = process.env.BACKEND_URL || "http://localhost:8000";

// CrewAI + Groq calls can take 30–90 s — tell the Vercel runtime not to cut us off.
export const maxDuration = 300;

async function proxy(req: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const { path: pathSegments } = await params;
  const path = pathSegments.join("/");
  const search = req.nextUrl.search;
  const upstreamUrl = `${BACKEND}/${path}${search}`;

  // For static image/zip assets served from /exports or /download-kit,
  // redirect the browser directly to the backend rather than streaming
  // through this serverless function — avoids the 4 MB / 10 MB body limit.
  if (
    req.method === "GET" &&
    (path.startsWith("exports/") || path.startsWith("download-kit/"))
  ) {
    return NextResponse.redirect(upstreamUrl, { status: 302 });
  }

  const headers = new Headers(req.headers);
  // Remove headers that should not be forwarded
  headers.delete("host");

  const init: RequestInit = {
    method: req.method,
    headers,
  };

  if (req.method !== "GET" && req.method !== "HEAD") {
    init.body = req.body as BodyInit;
    // Required for streaming request bodies in Node.js fetch
    (init as Record<string, unknown>).duplex = "half";
  }

  const upstream = await fetch(upstreamUrl, init);

  const resHeaders = new Headers(upstream.headers);
  // Strip hop-by-hop and encoding headers that would confuse the browser
  // when Next.js has already decompressed (or not) the upstream body.
  resHeaders.delete("transfer-encoding");
  resHeaders.delete("content-encoding");
  resHeaders.delete("content-length");

  return new NextResponse(upstream.body, {
    status: upstream.status,
    headers: resHeaders,
  });
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
export const HEAD = proxy;
export const OPTIONS = proxy;
