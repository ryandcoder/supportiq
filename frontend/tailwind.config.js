/** Editorial Analytics theme: colours come from CSS variables in src/index.css (light + dark). */
const c = (name) => `rgb(var(--${name}) / <alpha-value>)`;

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        paper: c("paper"),
        card: c("card"),
        ink: c("ink"),
        muted: c("muted"),
        line: c("line"),
        teal: { DEFAULT: c("teal"), soft: c("teal-soft") },
        good: c("good"),
        warn: c("warn"),
        bad: c("bad"),
      },
      fontFamily: {
        serif: ['"Source Serif 4"', "Georgia", "Cambria", "serif"],
        sans: ["Inter", "system-ui", "-apple-system", "Segoe UI", "sans-serif"],
      },
    },
  },
  plugins: [],
};
