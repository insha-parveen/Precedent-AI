import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Warm near-black ink on warm off-white canvas with sand borders,
        // complemented by DeepJudge's signature lavender and violet accents.
        ink: {
          DEFAULT: "#181816",
          light: "#262623",
          60: "rgba(24, 24, 22, 0.65)",
          40: "rgba(24, 24, 22, 0.4)",
        },
        canvas: "#f3f2ee",
        sand: {
          DEFAULT: "#e6e1d9",
          deep: "#d8d1c7",
        },
        paper: "#ffffff",
        lavender: {
          DEFAULT: "#f3f0fc",
          border: "#ded7f5",
        },
        violet: {
          DEFAULT: "#7c3aed",
          light: "#8b5cf6",
        },
        lilac: "#e8e2f8",
        dark: {
          surface: "#141412",
          card: "#1f1f1d",
          border: "#2e2e2a",
        },
        // Semantic risk colors
        risk: {
          low: "#2f6f4f",
          medium: "#9a6b1f",
          high: "#a33224",
        },
        citation: {
          bg: "#e6e1d9",
          hover: "#d8d1c7",
          border: "#c9c0b8",
        },
      },
      fontFamily: {
        sans: ["var(--font-archivo)", "system-ui", "sans-serif"],
        serif: ["Newsreader", "var(--font-merriweather)", "Georgia", "serif"],
        mono: ["var(--font-plex-mono)", "monospace"],
      },
      animation: {
        "fade-in": "fadeIn 0.2s ease-out",
        "slide-in-right": "slideInRight 0.3s ease-out",
        "slide-out-right": "slideOutRight 0.3s ease-in",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideInRight: {
          "0%": { transform: "translateX(100%)", opacity: "0" },
          "100%": { transform: "translateX(0)", opacity: "1" },
        },
        slideOutRight: {
          "0%": { transform: "translateX(0)", opacity: "1" },
          "100%": { transform: "translateX(100%)", opacity: "0" },
        },
      },
    },
  },
  plugins: [],
};
export default config;