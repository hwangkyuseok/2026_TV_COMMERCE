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
        "tv-bg": "#0a0a1a",
        "tv-panel": "#111128",
        "tv-card": "#1a1a35",
        "tv-focus": "#00e676",
        "tv-text": "#e0e0ff",
        "tv-muted": "#7070a0",
      },
    },
  },
  plugins: [],
};
export default config;
