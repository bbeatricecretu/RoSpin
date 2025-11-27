import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,       // Listen on all addresses, including LAN and Docker
    strictPort: true, // Exit if port 5173 is already in use
    port: 5173,       // Explicitly set the port
    watch: {
      usePolling: true, // <--- IMPORTANT: Fixes hot reload in Docker on Windows
    },
  },
})