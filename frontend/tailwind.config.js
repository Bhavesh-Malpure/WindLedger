/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#F7F9F7',
          100: '#D9F0E3',
          500: '#198754',
          600: '#146C43',
          700: '#123B32',
        },
        navy: {
          800: '#DCE5DE',
          900: '#FFFFFF',
          950: '#F7F9F7',
        }
      }
    },
  },
  plugins: [],
}
