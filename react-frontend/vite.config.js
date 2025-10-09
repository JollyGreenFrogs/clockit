import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Proxy API requests to FastAPI backend
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      },
      // Direct proxy for specific endpoints  
      '/auth': 'http://localhost:8001',
      '/tasks': 'http://localhost:8001',
      '/rates': 'http://localhost:8001',
      '/currency': 'http://localhost:8001',
      '/currencies': 'http://localhost:8001',
      '/categories': 'http://localhost:8001',
      '/invoice': 'http://localhost:8001',
      '/health': 'http://localhost:8001',
      '/version': 'http://localhost:8001',
      '/system': 'http://localhost:8001'
    }
  }
})
