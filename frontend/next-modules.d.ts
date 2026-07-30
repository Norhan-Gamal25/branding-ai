// next-modules.d.ts
// Ambient declarations for Next.js subpath modules.
// These are normally provided by next-env.d.ts + the next package's own types.
// This file silences TS7016 when the Next.js dist types are not fully installed.

declare module "next" {
  export * from "next/dist/server/next";

  export interface Metadata {
    title?: string;
    description?: string;
    keywords?: string | string[];
    authors?: Array<{ name?: string; url?: string }>;
    openGraph?: {
      title?: string;
      description?: string;
      type?: string;
      locale?: string;
      url?: string;
      siteName?: string;
      images?: Array<{ url: string; width?: number; height?: number; alt?: string }>;
    };
    twitter?: {
      card?: string;
      title?: string;
      description?: string;
      images?: string[];
    };
    [key: string]: unknown;
  }
}

declare module "next/server" {
  export { NextRequest, NextResponse } from "next/dist/server/web/exports";
}

declare module "next/navigation" {
  export function redirect(url: string, type?: "replace" | "push"): never;
  export function useRouter(): {
    push: (url: string) => void;
    replace: (url: string) => void;
    back: () => void;
    prefetch: (url: string) => void;
    refresh: () => void;
  };
  export function usePathname(): string;
  export function useSearchParams(): URLSearchParams;
}
