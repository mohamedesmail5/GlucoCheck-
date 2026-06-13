/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['Syne', 'sans-serif'],
        body:    ['IBM Plex Sans Arabic', 'sans-serif'],
        mono:    ['IBM Plex Mono', 'monospace'],
      },
      colors: {
        navy:  { DEFAULT: '#070d1a', 50: '#0d1629', 100: '#111e38', 200: '#1a2d50', 300: '#243c6a' },
        azure: { DEFAULT: '#0ea5e9', dark: '#0284c7', light: '#38bdf8' },
        jade:  { DEFAULT: '#10b981', dark: '#059669' },
        amber: { DEFAULT: '#f59e0b', dark: '#d97706' },
        rose:  { DEFAULT: '#f43f5e', dark: '#e11d48' },
        slate2: { DEFAULT: '#94a3b8', dark: '#64748b' }
      },
      backgroundImage: {
        'grid-pattern': "url(\"data:image/svg+xml,%3Csvg width='40' height='40' viewBox='0 0 40 40' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='%23ffffff' fill-opacity='0.02'%3E%3Cpath d='M0 0h40v1H0zM0 0v40h1V0z'/%3E%3C/g%3E%3C/svg%3E\")",
      },
      animation: {
        'fade-in':    'fadeIn 0.5s ease-out',
        'slide-up':   'slideUp 0.4s ease-out',
        'pulse-slow': 'pulse 3s ease-in-out infinite',
        'shimmer':    'shimmer 2s linear infinite',
      },
      keyframes: {
        fadeIn:  { from: { opacity: 0 }, to: { opacity: 1 } },
        slideUp: { from: { opacity: 0, transform: 'translateY(16px)' }, to: { opacity: 1, transform: 'translateY(0)' } },
        shimmer: { from: { backgroundPosition: '-200% 0' }, to: { backgroundPosition: '200% 0' } },
      }
    }
  },
  plugins: []
}
