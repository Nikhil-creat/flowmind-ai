import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Dark surface - used for the hero band and sidebar
        ink: "#0B0E1A",
        inkdeep: "#050710",
        // Light surface
        paper: "#F8F7FC",
        mist: "#E7E4F4",
        slatetext: "#4A4763",
        // Bold multi-color accent system - each color has one job, not decoration:
        violet: "#6C4CF1",   // primary brand / AI & intelligence features
        cyan: "#12B8C9",     // automation & workflow features
        coral: "#FF5D73",    // alerts, failures, destructive actions
        amber: "#F0A93E",    // success, highlights, the signal accent
        mint: "#22C58B",     // positive status, "active"/"ready" states
        // Backward-compatible aliases used by earlier components
        deep: "#6C4CF1",
        signal: "#F0A93E",
      },
      fontFamily: {
        display: ["var(--font-space-grotesk)", "sans-serif"],
        body: ["var(--font-inter)", "sans-serif"],
      },
      backgroundImage: {
        "hero-gradient": "linear-gradient(135deg, #6C4CF1 0%, #12B8C9 100%)",
        "brand-gradient": "linear-gradient(90deg, #6C4CF1 0%, #FF5D73 100%)",
      },
      borderRadius: {
        sm: "6px",
        md: "10px",
        lg: "16px",
      },
    },
  },
  plugins: [],
};

export default config;
