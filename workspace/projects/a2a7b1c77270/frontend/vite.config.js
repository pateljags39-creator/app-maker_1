import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000', // Your FastAPI backend
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '/api'), // Ensure the /api prefix is kept for the backend
      },
    },
  },
});