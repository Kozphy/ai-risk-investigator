import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0f172a",
        slatepanel: "#1e293b",
        accent: "#0d9488",
        warn: "#b45309",
        danger: "#b91c1c",
      },
      fontFamily: {
        sans: ["var(--font-geist-sans)", "Segoe UI", "sans-serif"],
        display: ["var(--font-source-serif)", "Georgia", "serif"],
      },
    },
  },
  plugins: [],
};

export default config;
