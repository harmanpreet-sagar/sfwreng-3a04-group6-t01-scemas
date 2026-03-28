/**
 * Vite Configuration
 * Configures the build tool and dev server for the React frontend
 */

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  // Enable React plugin for JSX transformation and Fast Refresh
  plugins: [react()],
  
  // Development server configuration
  server: {
    host: '0.0.0.0',  // Bind to all network interfaces (required for Docker)
    port: 3000,       // Standard development port
  },
})
