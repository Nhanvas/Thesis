import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Same-origin from the browser's perspective — avoids CORS/cookie edge cases
    // during `npm run dev`. Backend runs separately on :8000 (see main.py).
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
})
