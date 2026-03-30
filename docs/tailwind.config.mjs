import typography from "@tailwindcss/typography";

/** @type {import('tailwindcss').Config} */
export default {
  content: ["./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}"],
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        sans: [
          "Inter",
          "Hiragino Sans",
          "Hiragino Kaku Gothic ProN",
          "Noto Sans JP",
          "system-ui",
          "sans-serif",
        ],
      },
      colors: {
        ink: {
          50: "#f7f8fb",
          100: "#eef0f6",
          200: "#d8dce8",
          300: "#b4bbd0",
          400: "#8a93ad",
          500: "#6b7390",
          600: "#555b73",
          700: "#464a5e",
          800: "#2e3140",
          900: "#1a1c26",
          950: "#0f1016",
        },
        accent: {
          DEFAULT: "#3b82f6",
          dim: "#2563eb",
          glow: "#60a5fa",
        },
      },
      boxShadow: {
        soft: "0 4px 24px -4px rgb(0 0 0 / 0.08), 0 8px 32px -8px rgb(0 0 0 / 0.12)",
        "soft-dark":
          "0 4px 24px -4px rgb(0 0 0 / 0.35), 0 8px 32px -8px rgb(0 0 0 / 0.45)",
      },
    },
  },
  plugins: [typography],
};
