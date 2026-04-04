/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"DM Sans"', 'system-ui', 'sans-serif'],
        display: ['Fraunces', 'Georgia', 'serif'],
      },
      colors: {
        ink: {
          50: '#f4f6f9',
          100: '#e8ecf2',
          200: '#d1d9e5',
          300: '#a8b5ca',
          400: '#7a8aad',
          500: '#5c6b8f',
          600: '#495572',
          700: '#3c465e',
          800: '#343c50',
          900: '#1e2433',
          950: '#0f131d',
        },
        parchment: {
          DEFAULT: '#f7f4ef',
          deep: '#efe9df',
          muted: '#e8e2d6',
        },
        moss: {
          50: '#effaf4',
          100: '#d8f2e3',
          200: '#b4e4ca',
          300: '#82cfa8',
          400: '#4db382',
          500: '#2f8f65',
          600: '#237352',
          700: '#1d5c44',
          800: '#1a4a38',
          900: '#173d30',
        },
        honey: {
          300: '#f5e6a8',
          400: '#e9cf6e',
          500: '#d4a84b',
          600: '#b8862f',
        },
        brand: {
          50: '#f0fdfa',
          100: '#ccfbf1',
          400: '#2dd4bf',
          500: '#14b8a6',
          600: '#0d9488',
          700: '#0f766e',
          900: '#134e4a',
        },
      },
      boxShadow: {
        card: '0 1px 2px rgb(15 19 29 / 0.04), 0 6px 20px rgb(15 19 29 / 0.06)',
        'card-lg': '0 4px 8px rgb(15 19 29 / 0.04), 0 16px 40px rgb(15 19 29 / 0.09)',
        lift: '0 2px 8px rgb(47 143 101 / 0.12), 0 12px 32px rgb(15 19 29 / 0.08)',
        insetWarm: 'inset 0 1px 0 rgb(255 255 255 / 0.65)',
      },
      backgroundImage: {
        'noise-soft':
          "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.04'/%3E%3C/svg%3E\")",
        'mesh-hero':
          'radial-gradient(ellipse 100% 80% at 20% 20%, rgb(47 143 101 / 0.35), transparent 55%), radial-gradient(ellipse 70% 60% at 85% 10%, rgb(212 168 75 / 0.18), transparent 50%), radial-gradient(ellipse 60% 50% at 70% 90%, rgb(20 184 166 / 0.12), transparent 45%)',
      },
    },
  },
  plugins: [],
};
