// lib/utils.ts
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Determine if a locale is RTL */
export const RTL_LOCALES = new Set([
  "ar", "he", "fa", "ur", "ps", "ku", "yi", "dv", "ug",
]);

export function isRTL(locale: string): boolean {
  return RTL_LOCALES.has(locale.split("-")[0]);
}

/** Map ISO 639-1 code → display name */
export const LANGUAGES: Record<string, string> = {
  auto: "Auto-detect",
  en: "English",
  ar: "العربية",
  fr: "Français",
  es: "Español",
  tr: "Türkçe",
  ur: "اردو",
  id: "Bahasa Indonesia",
  ms: "Bahasa Melayu",
  bn: "বাংলা",
  sw: "Kiswahili",
  ha: "Hausa",
  so: "Soomaali",
  fa: "فارسی",
  ps: "پښتو",
  az: "Azərbaycan",
  uz: "Oʻzbek",
  kk: "Қазақ",
  de: "Deutsch",
  nl: "Nederlands",
  pt: "Português",
  it: "Italiano",
  ru: "Русский",
  zh: "中文",
  ja: "日本語",
  ko: "한국어",
  hi: "हिन्दी",
};

/** Copy text to clipboard */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    return false;
  }
}
