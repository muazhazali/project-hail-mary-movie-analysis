/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        surface: "#0b0c10",
        panel: "#1f2833",
        accent: "#66fcf1",
        accent2: "#45a29e",
        muted: "#c5c6c7",
        danger: "#e74c3c",
        success: "#2ecc71",
      },
      fontFamily: {
        display: ['"Orbitron"', 'sans-serif'],
        body: ['"Space Mono"', 'monospace'],
      },
    },
  },
  plugins: [],
}
