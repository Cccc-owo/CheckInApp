import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],

  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },

  server: {
    host: '0.0.0.0',  // Listen on all network interfaces for LAN access
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },

  build: {
    outDir: 'dist',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks(id) {
          // Manual chunking for better dependency management
          if (id.includes('node_modules')) {
            // Ant Design Vue
            if (id.includes('ant-design-vue')) {
              return 'ant-design-vue'
            }
            // Group all other vendor code together
            return 'vendor'
          }
        },
      },
    },
  },
})
