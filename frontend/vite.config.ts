import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// envDir "..": reads VITE_API_URL from the .env in the project root
export default defineConfig({
  plugins: [react()],
  envDir: "..",
  server: { port: 5173, host: true },
  test: { environment: "node", include: ["src/**/*.test.ts"] },
});
