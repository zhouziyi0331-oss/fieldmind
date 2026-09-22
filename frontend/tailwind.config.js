/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        // 主色调 - 蓝绿系
        primary: {
          DEFAULT: "#27768A",
          light: "#589DA4",
          lighter: "#93AEC1",
          dark: "#1E5A6B",
        },
        // 次色调 - 绿色系
        secondary: {
          DEFAULT: "#748D44",
          light: "#85A156",
          lighter: "#9FAC24",
        },
        // 强调色 - 金色/橙色
        accent: {
          gold: "#F8B042",
          orange: "#D9BC92",
          coral: "#EC6A52",
        },
        // 语义化颜色
        success: "#85A156",
        warning: "#F8B042",
        error: "#EC6A52",
        info: "#589DA4",
        // 背景色
        background: "#F8FAFB",
        surface: "#FFFFFF",
        "surface-hover": "#F0F5E2",
        // 文字颜色
        text: {
          primary: "#1A1A1A",
          secondary: "#666666",
          tertiary: "#999999",
        },
        // 边框颜色
        border: {
          DEFAULT: "#E5E7EB",
          hover: "#589DA4",
        },
      },
      borderRadius: {
        sm: "4px",
        DEFAULT: "8px",
        md: "8px",
        lg: "12px",
        xl: "16px",
      },
      boxShadow: {
        sm: "0 1px 2px rgba(39, 118, 138, 0.05)",
        DEFAULT: "0 4px 6px rgba(39, 118, 138, 0.08)",
        md: "0 4px 6px rgba(39, 118, 138, 0.08)",
        lg: "0 10px 15px rgba(39, 118, 138, 0.1)",
        xl: "0 20px 25px rgba(39, 118, 138, 0.12)",
      },
      spacing: {
        xs: "4px",
        sm: "8px",
        md: "16px",
        lg: "24px",
        xl: "32px",
        "2xl": "48px",
      },
      keyframes: {
        "fade-in": {
          from: { opacity: 0 },
          to: { opacity: 1 },
        },
        "fade-out": {
          from: { opacity: 1 },
          to: { opacity: 0 },
        },
        "slide-in-up": {
          from: { transform: "translateY(10px)", opacity: 0 },
          to: { transform: "translateY(0)", opacity: 1 },
        },
        "slide-in-down": {
          from: { transform: "translateY(-10px)", opacity: 0 },
          to: { transform: "translateY(0)", opacity: 1 },
        },
        "scale-in": {
          from: { transform: "scale(0.95)", opacity: 0 },
          to: { transform: "scale(1)", opacity: 1 },
        },
        "pulse-subtle": {
          "0%, 100%": { opacity: 1 },
          "50%": { opacity: 0.8 },
        },
      },
      animation: {
        "fade-in": "fade-in 0.2s ease-out",
        "fade-out": "fade-out 0.2s ease-out",
        "slide-in-up": "slide-in-up 0.3s ease-out",
        "slide-in-down": "slide-in-down 0.3s ease-out",
        "scale-in": "scale-in 0.2s ease-out",
        "pulse-subtle": "pulse-subtle 2s ease-in-out infinite",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
