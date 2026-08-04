/**
 * Tailwind CSS configuration — Script Doctor Swarm
 *
 * NOTE: This project uses Tailwind CSS v4 via the @tailwindcss/vite plugin.
 * In Tailwind v4 the design tokens are defined in CSS via `@theme` in
 * `src/index.css`; this config file is retained for documentation and
 * tooling compatibility (IDE autocomplete, etc.).
 *
 * Design Direction: physical studio coverage folder, not SaaS dashboard.
 * Palette from plan §5.5:
 *   paper   #F7F3E8  — page background
 *   ink     #1F1B16  — primary text / borders
 *   manila  #D4B483  — warm accent (folder tabs, manila paper tones)
 *   flag    #C1381F  — grease-pencil red (PASS verdict + flag accents only)
 *   carbon  #3A5A78  — carbon-copy blue (Structure agent accent)
 *   stamp   #4B5D3A  — stamp green (RECOMMEND verdict only)
 *
 * Typography:
 *   script/courier  "Courier Prime"  — screenplay text, beat evidence quotes
 *   sans/grotesk    "IBM Plex Sans"  — UI chrome, labels, body copy
 */

/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#F7F3E8",
        ink: "#1F1B16",
        manila: "#D4B483",
        flag: "#C1381F",
        "red-flag": "#C1381F",
        carbon: "#3A5A78",
        "carbon-blue": "#3A5A78",
        stamp: "#4B5D3A",
        "stamp-green": "#4B5D3A",
      },
      fontFamily: {
        script: ['"Courier Prime"', "Courier", "monospace"],
        courier: ['"Courier Prime"', "Courier", "monospace"],
        sans: ['"IBM Plex Sans"', "Inter", "sans-serif"],
        grotesk: ['"IBM Plex Sans"', "Inter", "sans-serif"],
      },
    },
  },
  plugins: [],
};
