/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        pearl: {
          DEFAULT: '#F6F8FC',
          subtle: '#EEF2FA',
          muted: '#E2E8F4',
        },
        cobalt: {
          DEFAULT: '#3867E9',
          hover: '#2952C8',
          soft: '#EAF0FE',
          50: '#F3F6FE',
          100: '#EAF0FE',
          700: '#3867E9',
          800: '#2952C8',
        },
        mint: {
          DEFAULT: '#22A995',
          dark: '#127466',
          soft: '#E6F6F3',
          border: '#99DDD2',
        },
        champagne: {
          DEFAULT: '#D69B42',
          dark: '#8A5B14',
          soft: '#FBF4E7',
          border: '#EBD09F',
        },
        ivory: {
          DEFAULT: '#F6F8FC',
          subtle: '#EEF2FA',
          muted: '#E2E8F4',
        },
        forest: {
          DEFAULT: '#3867E9',
          hover: '#2952C8',
          soft: '#EAF0FE',
          50: '#F3F6FE',
          100: '#EAF0FE',
          700: '#3867E9',
          800: '#2952C8',
          900: '#1F3FA3',
        },
        lime: {
          nexora: '#22A995',
          hover: '#198777',
          soft: '#E6F6F3',
        },
        ink: {
          DEFAULT: '#202B43',
          muted: '#4E5D78',
          subtle: '#5E6D87',
        },
        borderc: {
          DEFAULT: '#E2E8F4',
          strong: '#CBD5E6',
        },
      },
      fontFamily: {
        heading: ['Sora', 'Inter', 'system-ui', 'sans-serif'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'monospace'],
      },
      boxShadow: {
        card: '0 1px 2px rgba(32, 43, 67, 0.04), 0 8px 24px -12px rgba(56, 103, 233, 0.08)',
        elevated: '0 4px 16px rgba(32, 43, 67, 0.06), 0 18px 40px -16px rgba(56, 103, 233, 0.14)',
      },
      borderRadius: {
        '2xl': '1rem',
        '3xl': '1.5rem',
      },
    },
  },
  plugins: [],
}
