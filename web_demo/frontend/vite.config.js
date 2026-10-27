import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Fixed port, no silent fallback: backend's CORS allowlist (main.py) only accepts
    // :5173, so a silent fallback to :5174 would make login fail with an opaque CORS
    // error instead of a clear "port in use" message.
    port: 5173,
    strictPort: true,
    // Same-origin from the browser's perspective — avoids CORS/cookie edge cases
    // during `npm run dev`. Backend runs separately on :8000 (see main.py).
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
})
