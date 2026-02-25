/// <reference types="vitest/config" />
import { resolve } from "node:path"
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": resolve(__dirname, "./src"),
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-3d': [
            'three',
            '@react-three/fiber',
            '@react-three/drei',
            '@react-three/postprocessing',
          ],
          'vendor-particles': [
            '@tsparticles/react',
            '@tsparticles/slim',
          ],
          'vendor-motion': ['motion'],
          'vendor-charts': ['recharts'],
          'vendor-xyflow': ['@xyflow/react', '@xyflow/system'],
        },
      },
    },
  },
  server: {
    proxy: {
      '/api': 'http://localhost:8400',
      '/ws': { target: 'ws://localhost:8400', ws: true },
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    css: false,
  },
})
