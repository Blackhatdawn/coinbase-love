import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { componentTagger } from "lovable-tagger";

// ============================================
// VITE CONFIGURATION - CryptoVault Frontend
// Enterprise-Grade Production-Ready Setup
// ============================================
// This config enables:
// 1. Development proxy to local backend (port 8001)
// 2. WebSocket proxy for real-time price feeds (/socket.io)
// 3. Production build optimizations and code splitting
// 4. Zero-hardcoding of sensitive URLs (uses env vars)
// 5. Proper error handling and fallbacks
// ============================================

// Backend URL for development proxy
// Falls back to localhost:8001 if VITE_BACKEND_URL not set
// In production, Vercel rewrites handle all proxying via vercel.json
const BACKEND_URL = process.env.VITE_BACKEND_URL || "http://localhost:8001";

// Validate backend URL in development
if (process.env.NODE_ENV === "development") {
  console.log(`[Vite] Backend proxy configured for: ${BACKEND_URL}`);
}

export default defineConfig(({ mode }) => ({
  define: {
    __VERSION__: JSON.stringify(process.env.npm_package_version),
  },
  build: {
    outDir: 'dist',
    minify: 'terser',
    sourcemap: mode !== 'production',
    target: 'ES2020',
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        manualChunks: (id) => {
          // Vendor chunk
          if (id.includes('node_modules')) {
            // Sentry should be in its own chunk
            if (id.includes('@sentry')) {
              return 'sentry-vendor';
            }
            if (id.includes('ethers')) {
              return 'web3-vendor';
            }
            if (id.includes('@radix-ui') || id.includes('cmdk') || id.includes('sonner')) {
              return 'ui-vendor';
            }
            // Separate chart libraries to avoid circular dependencies
            if (id.includes('recharts')) {
              return 'recharts-vendor';
            }
            if (id.includes('lightweight-charts')) {
              return 'tradingview-vendor';
            }
            if (id.includes('chart.js') || id.includes('react-chartjs-2')) {
              return 'chartjs-vendor';
            }
            if (id.includes('@tanstack/react-query') || id.includes('axios')) {
              return 'data-vendor';
            }
            return 'vendor';
          }
          // Page chunks
          if (id.includes('/pages/')) {
            const match = id.match(/\/pages\/(\w+)\./);
            if (match) {
              return `pages/${match[1]}`;
            }
          }
          // Context and utilities chunk
          if (id.includes('/contexts/') || id.includes('/hooks/')) {
            return 'core';
          }
        },
      },
    },
    terserOptions: {
      compress: {
        drop_console: mode === 'production',
        drop_debugger: mode === 'production',
      },
    },
  },
  server: {
    port: 3000,
    host: '0.0.0.0',
    allowedHosts: true,
    // ============================================
    // DEVELOPMENT PROXY CONFIGURATION
    // ============================================
    // Routes /api/* and /socket.io/* to local backend
    // In production, Vercel handles this via rewrites
    // ============================================
    proxy: {
      // API endpoints proxy
      "/api": {
        target: BACKEND_URL,
        changeOrigin: true,
        secure: false,
        // Rewrite is not needed since backend expects /api prefix
        // rewrite: (path) => path.replace(/^\/api/, '/api'),
      },
      // WebSocket proxy for Socket.IO
      "/socket.io": {
        target: BACKEND_URL,
        changeOrigin: true,
        secure: false,
        ws: true, // Enable WebSocket proxy
      },
      // Health check proxy
      "/health": {
        target: BACKEND_URL,
        changeOrigin: true,
        secure: false,
      },
      // Ping endpoint proxy
      "/ping": {
        target: BACKEND_URL,
        changeOrigin: true,
        secure: false,
      },
      // CSRF token endpoint proxy
      "/csrf": {
        target: BACKEND_URL,
        changeOrigin: true,
        secure: false,
      },
    },
  },
  plugins: [react(), mode === "development" && componentTagger()].filter(Boolean),
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  // Production optimizations
  ...(mode === 'production' && {
    esbuild: {
      drop: ['console', 'debugger'],
    },
    // Enable compression reporting
    reportCompressedSize: true,
    // Better tree-shaking
    rollupOptions: {
      output: {
        // Generate source maps for production error tracking
        sourcemap: 'hidden', // Don't expose to users but available for error tracking
      },
    },
  }),

  // Performance hints
  rollupOptions: {
    output: {
      // Ensure predictable chunk names for caching
      assetFileNames: 'assets/[name].[hash][extname]',
      chunkFileNames: 'chunks/[name].[hash].js',
      entryFileNames: 'js/[name].[hash].js',
    },
  },

  // HTTP/2 Push configuration (automatically handled by Vercel)
  // If using custom server, enable in production HTTP server config
}));
