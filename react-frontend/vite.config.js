/// <reference types="vitest" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.js',
    css: true,
    exclude: ['node_modules', 'e2e/**'],
  },
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
