import type { Config } from 'tailwindcss';
import animatePlugin from 'tailwindcss-animate';

const config: Config = {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        background: '#0b0f1a',
        surface: '#0f1424',
        border: '#1f2a44',
        slate: {
          950: '#06070d',
        },
        indigo: {
          400: '#6366f1',
          500: '#4f46e5',
          600: '#4338ca',
        },
        emerald: {
          400: '#34d399',
          500: '#10b981',
          600: '#059669',
        },
      },
      borderRadius: {
        xl: '1rem',
        '2xl': '1.25rem',
      },
      boxShadow: {
        soft: '0 10px 40px -20px rgba(15, 20, 36, 0.8)',
        card: '0 20px 60px -30px rgba(33, 48, 84, 0.45)',
      },
      fontFamily: {
        sans: [
          'Inter',
          '-apple-system',
          'BlinkMacSystemFont',
          '\'Segoe UI\'',
          'sans-serif',
        ],
      },
    },
  },
  plugins: [animatePlugin],
};

export default config;
