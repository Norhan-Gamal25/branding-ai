import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans:    ["Inter",    "system-ui", "sans-serif"],
        display: ["Syne",     "system-ui", "sans-serif"],
        mono:    ["JetBrains Mono", "Fira Code", "monospace"],
      },
      colors: {
        /* Brand */
        accent:  "#7c6dfa",
        "accent-deep": "#5b4de0",
        gold:    "#e8b84b",
        "gold-light": "#f0ca74",

        /* Semantic surfaces */
        surface:  "#0d0d16",
        elevated: "#13131e",
        card:     "#171724",
        "studio-border": "#252535",

        /* Status */
        emerald:  "#34d399",
        rose:     "#fb7185",
        amber:    "#fbbf24",
      },
      boxShadow: {
        "glow-accent": "0 0 20px rgba(124,109,250,0.22), 0 0 60px rgba(124,109,250,0.08)",
        "glow-gold":   "0 0 20px rgba(232,184,75,0.25),  0 0 60px rgba(232,184,75,0.08)",
        "glow-emerald":"0 0 10px rgba(52,211,153,0.3)",
        "card-hover":  "0 8px 32px rgba(124,109,250,0.12)",
      },
      backgroundImage: {
        "mesh-dark": `
          radial-gradient(ellipse 90% 70% at 15% 5%,  rgba(124,109,250,0.10) 0%, transparent 55%),
          radial-gradient(ellipse 60% 50% at 85% 90%, rgba(232,184,75,0.07)  0%, transparent 55%),
          radial-gradient(ellipse 50% 40% at 50% 50%, rgba(52,211,153,0.03)  0%, transparent 60%)
        `,
        "gradient-accent": "linear-gradient(135deg, #7c6dfa, #5b4de0)",
        "gradient-brand":  "linear-gradient(135deg, #f0eff8 0%, #7c6dfa 48%, #e8b84b 100%)",
        "gradient-gold":   "linear-gradient(135deg, #f0ca74 0%, #e8b84b 60%, #c47a2a 100%)",
      },
      animation: {
        "bounce-slow": "bounce-slow 1.4s ease-in-out infinite",
        "pulse-dot":   "pulse-dot 2s ease-in-out infinite",
        "spin-slow":   "spin 3s linear infinite",
      },
      keyframes: {
        "bounce-slow": {
          "0%, 100%": { transform: "translateY(0)" },
          "50%":       { transform: "translateY(-4px)" },
        },
        "pulse-dot": {
          "0%, 100%": { opacity: "1",   transform: "scale(1)"    },
          "50%":       { opacity: "0.5", transform: "scale(0.85)" },
        },
      },
      borderRadius: {
        "2xl": "1rem",
        "3xl": "1.5rem",
      },
    },
  },
  plugins: [],
};

export default config;
