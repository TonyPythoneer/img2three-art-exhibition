import { defineConfig } from "vite-plus";
import vue from "@vitejs/plugin-vue";
import tailwindcss from "@tailwindcss/vite";
import VueRouter from "vue-router/vite";
import velite from "@velite/plugin-vite";
import { fileURLToPath } from "node:url";
import { exhibitSlugs } from "./src/exhibits/slugs.js";

// `ssgOptions` is read by vite-ssg at build time, but vite-plus's defineConfig type does
// not model it, so the argument is asserted. Every other key is still structurally checked.
export default defineConfig({
  // A GitHub *project* page, not a user page: the site is served from /<repo>/, so every
  // asset URL needs the prefix. Change this and the deploy target has to change with it.
  base: "/img2three-art-exhibition/",
  plugins: [
    tailwindcss(),
    VueRouter({ routesFolder: "src/pages", dts: "typed-router.d.ts" }),
    vue(),
    velite({ config: "velite.config.ts" }),
  ],
  define: {
    __VUE_OPTIONS_API__: "false",
    __VUE_PROD_DEVTOOLS__: "false",
    __VUE_PROD_HYDRATION_MISMATCH_DETAILS__: "false",
  },
  resolve: {
    alias: [{ find: "~", replacement: fileURLToPath(new URL("./src", import.meta.url)) }],
  },
  server: { port: 3000 },
  // `vp config` (the `prepare` script) installs a pre-commit hook that runs `vp staged`.
  // Without this key the hook rejects every commit.
  staged: {
    "*": "vp check --fix",
  },
  fmt: {
    ignorePatterns: ["dist/**", "src/exhibits/**/*.md"],
  },
  ssgOptions: {
    // "nested" emits dist/balamb-garden/index.html. The default "flat" emits
    // balamb-garden.html, which not every static host serves at /balamb-garden.
    dirStyle: "nested",
    // An allowlist, not a filter, so a new page is never prerendered by accident.
    // /render-harness must stay out of it: it mounts WebGL, and prerendering
    // would evaluate Three.js in node where there is no GL context. The capture
    // harness reaches it through the SPA fallback in tools/capture.mjs instead.
    includedRoutes: () => ["/", "/progress", ...exhibitSlugs.map((s) => `/${s}`)],
  },
} as Parameters<typeof defineConfig>[0]);
