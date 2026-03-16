import type { Config } from "tailwindcss";
const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: "#C0392B",
          dark: "#922B21",
          light: "#F9EBEA",
          50: "#FEF2F2",
          100: "#FDE8E8",
          500: "#C0392B",
          600: "#A93226",
          700: "#922B21",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
export default config;
