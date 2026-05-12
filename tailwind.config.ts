import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Manrope', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        bg: '#F7F8FB',
        'bg-alt': '#EEF1F7',
        paper: '#FFFFFF',
        ink: '#0B1220',
        'ink-2': '#1F2937',
        mute: '#5E6B82',
        faint: '#97A1B5',
        line: '#E6EAF2',
        'line-2': '#D0D7E6',
        brand: '#2563EB',
        'brand-deep': '#0B1E47',
        'brand-soft': '#EEF3FE',
        lime: '#FFDD55',
        'accent-2': '#93C5FD',
        page: '#F4F2EC',
      },
      letterSpacing: {
        tighter: '-0.035em',
        display: '-0.035em',
        mono: '0.08em',
      },
      lineHeight: {
        display: '0.98',
      },
      borderRadius: {
        '2xl': '1rem',
        '3xl': '1.25rem',
        '4xl': '1.5rem',
      },
      keyframes: {
        fadeUp: {
          from: { opacity: '0', transform: 'translateY(14px)' },
          to:   { opacity: '1', transform: 'translateY(0)' },
        },
        pulse: {
          '0%, 100%': { opacity: '1' },
          '50%':       { opacity: '0.55' },
        },
        dotPulse: {
          '0%, 100%': { transform: 'scale(1)',   opacity: '1' },
          '50%':       { transform: 'scale(0.6)', opacity: '0.5' },
        },
      },
      animation: {
        'fade-up':   'fadeUp 0.6s ease both',
        'fade-up-1': 'fadeUp 0.6s 0.08s ease both',
        'fade-up-2': 'fadeUp 0.6s 0.16s ease both',
        'fade-up-3': 'fadeUp 0.6s 0.24s ease both',
        'fade-up-4': 'fadeUp 0.6s 0.32s ease both',
        'pulse-slow': 'pulse 1.4s ease-in-out infinite',
        'dot-pulse':  'dotPulse 1.6s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}

export default config
