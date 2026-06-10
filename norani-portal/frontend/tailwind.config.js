/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        norani: {
          blue: "#1F4E79",
          "blue-light": "#2E75B6",
          "blue-bg": "#EFF6FB",
          orange: "#F57C00",
          "orange-light": "#FFB74D",
          surface: "#F5F8FB",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
        serif: ["Georgia", "serif"],
      },
    },
  },
  plugins: [],
};
