import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  // GitHub Pages 部署於子路徑（VITE_BASE）；本機開發維持 "/"。
  base: process.env.VITE_BASE ?? "/",
  server: { port: 5173 },
});
