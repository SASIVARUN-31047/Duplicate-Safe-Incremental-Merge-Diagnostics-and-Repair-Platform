/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f8fafc',
          100: '#f1f5f9',
          500: '#3b82f6',
          700: '#1d4ed8',
          900: '#0f172a',
        },
        quarantine: {
          light: '#fef3c7',
          DEFAULT: '#d97706',
          dark: '#78350f',
        },
        resolved: {
          light: '#d1fae5',
          DEFAULT: '#059669',
          dark: '#064e3b',
        }
      },
    },
  },
  plugins: [],
};
