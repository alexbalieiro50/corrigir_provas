import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Encaminha chamadas /api para o backend FastAPI durante o desenvolvimento
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
