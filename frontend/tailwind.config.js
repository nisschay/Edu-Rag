/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          900: '#0a0a0b',
          800: '#111113',
          700: '#18181b',
          600: '#27272a',
          500: '#3f3f46',
          400: '#52525b',
        },
        accent: {
          primary: '#6366f1',
          hover: '#818cf8',
          muted: '#4f46e5',
        }
      }
    },
  },
  plugins: [],
}
