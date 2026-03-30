import { defineConfig } from "astro/config";
import tailwind from "@astrojs/tailwind";

const rawBase = (process.env.PUBLIC_BASE_PATH || "").trim();
const base =
  rawBase === "" || rawBase === "/"
    ? undefined
    : rawBase.startsWith("/")
      ? rawBase.replace(/\/$/, "") || "/"
      : `/${rawBase.replace(/\/$/, "")}`;

export default defineConfig({
  site: process.env.PUBLIC_SITE_URL?.trim() || undefined,
  base,
  integrations: [tailwind({ applyBaseStyles: true })],
  outDir: "dist",
});
