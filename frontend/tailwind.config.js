/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Apple 系統色
        risk: {
          green: "#34C759",
          yellow: "#FF9F0A",
          red: "#FF3B30",
        },
        ink: "#1D1D1F", // 深炭灰文字
        canvas: "#F5F5F7", // 近白背景
        subtle: "#86868B", // 次要文字
      },
      fontFamily: {
        sans: [
          "-apple-system",
          "BlinkMacSystemFont",
          "PingFang TC",
          "Noto Sans TC",
          "Segoe UI",
          "Helvetica Neue",
          "sans-serif",
        ],
      },
      boxShadow: {
        card: "0 1px 3px rgba(0,0,0,0.06), 0 6px 24px rgba(0,0,0,0.04)",
      },
      borderRadius: {
        "2xl": "1.25rem",
      },
    },
  },
  plugins: [],
};
