/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        surface: '#0f1117',
        card: '#1a1d27',
        border: '#2a2d3a',
        accent: '#6366f1',
        positive: '#22c55e',
        negative: '#ef4444',
        warning: '#f59e0b',
        muted: '#6b7280',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
    },
  },
  plugins: [],
}

