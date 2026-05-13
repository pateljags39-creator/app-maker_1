/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#4F46E5', // Indigo 600
        secondary: '#6366F1', // Indigo 500
        accent: '#EC4899', // Pink 500
        background: '#F9FAFB', // Gray 50
        text: '#1F2937', // Gray 900
        'text-light': '#6B7280', // Gray 500
        border: '#E5E7EB', // Gray 200
        success: '#10B981', // Green 500
        warning: '#F59E0B', // Amber 500
        danger: '#EF4444', // Red 500
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
      boxShadow: {
        'card': '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
        'lg': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
      },
    },
  },
  plugins: [],
}