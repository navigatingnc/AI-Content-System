import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'static', // Output directory for the build
    emptyOutDir: true, // Ensure the output directory is emptied before each build
  },
  server: {
    // Optional: configure a proxy if the frontend needs to call the backend API
    // during development (e.g., Flask server running on port 5000)
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      }
    }
  }
})
