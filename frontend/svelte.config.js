import adapter from "@sveltejs/adapter-static";
import { vitePreprocess } from "@sveltejs/vite-plugin-svelte";

/** @type {import('@sveltejs/kit').Config} */
const config = {
  preprocess: vitePreprocess(),
  kit: {
    adapter: adapter({
      pages: "../backend/app/static",
      assets: "../backend/app/static",
      fallback: "index.html", // Essential for SPA routing
      precompress: false,
      strict: true,
    }),
    alias: {
      "@/*": "./path/to/lib/*",
    },
  },
};

export default config;
