/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0d1117',
        surface: '#161b22',
        surfaceHover: '#21262d',
        border: '#30363d',
        accent: '#58a6ff',
        success: '#238636',
        warning: '#d29922',
        danger: '#da3633',
        textMuted: '#8b949e',
        textMain: '#c9d1d9',
      }
    },
  },
  plugins: [],
}
