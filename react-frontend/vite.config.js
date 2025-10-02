import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Proxy API requests to FastAPI backend
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      },
      // Direct proxy for specific endpoints  
      '/auth': 'http://localhost:8000',
      '/tasks': 'http://localhost:8000',
      '/rates': 'http://localhost:8000',
      '/currency': 'http://localhost:8000',
      '/invoice': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
      '/categories': 'http://localhost:8000',
      '/planner': 'http://localhost:8000'
    }
  }
})
