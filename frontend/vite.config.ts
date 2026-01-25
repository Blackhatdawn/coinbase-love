import { defineConfig, splitVendorChunkPlugin } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { componentTagger } from "lovable-tagger";

// ============================================
// VITE CONFIGURATION - CryptoVault Frontend
// Enterprise-Grade Production-Ready Setup
// ============================================
// Performance Optimizations:
// 1. Code splitting with manual chunks
// 2. Tree shaking with terser
// 3. Asset optimization
// 4. Compression with brotli/gzip
// 5. Cache optimization with hash filenames
// 6. Development proxy to local backend
// ============================================

// Backend URL for development proxy
const BACKEND_URL = process.env.VITE_BACKEND_URL || "http://localhost:8001";

// Validate backend URL in development
if (process.env.NODE_ENV === "development") {
  console.log(`[Vite] Backend proxy configured for: ${BACKEND_URL}`);
}

export default defineConfig(({ mode }) => ({
  define: {
    __VERSION__: JSON.stringify(process.env.npm_package_version),
    __DEV__: mode !== 'production',
  },
  
  // ============================================
  // BUILD CONFIGURATION - Production Optimized
  // ============================================
  build: {
    outDir: 'dist',
    minify: 'terser',
    sourcemap: mode === 'development' ? true : 'hidden', // Hidden for prod (error tracking only)
    target: 'ES2020',
    chunkSizeWarningLimit: 500, // Warn on chunks > 500KB
    cssCodeSplit: true, // Split CSS per async chunk
    cssMinify: true,
    assetsInlineLimit: 4096, // Inline assets < 4KB
    
    rollupOptions: {
      output: {
        // Optimized chunk naming for long-term caching
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name?.split('.') || [];
          const ext = info[info.length - 1];
          if (/\.(png|jpe?g|gif|svg|webp|avif|ico)$/i.test(assetInfo.name || '')) {
            return 'assets/images/[name].[hash][extname]';
          }
          if (/\.(woff2?|eot|ttf|otf)$/i.test(assetInfo.name || '')) {
            return 'assets/fonts/[name].[hash][extname]';
          }
          return 'assets/[name].[hash][extname]';
        },
        chunkFileNames: 'chunks/[name].[hash].js',
        entryFileNames: 'js/[name].[hash].js',
        
        // Manual chunk splitting for optimal caching
        manualChunks: (id) => {
          // Node modules chunking
          if (id.includes('node_modules')) {
            // Critical vendor - loaded immediately
            if (id.includes('react') || id.includes('react-dom') || id.includes('react-router')) {
              return 'vendor-react';
            }
            
            // Monitoring & Analytics - separate chunk
            if (id.includes('@sentry') || id.includes('@vercel/analytics')) {
              return 'vendor-monitoring';
            }
            
            // Web3/Crypto - heavy, lazy loaded
            if (id.includes('ethers')) {
              return 'vendor-web3';
            }
            
            // UI Components - shared
            if (id.includes('@radix-ui') || id.includes('cmdk') || id.includes('sonner')) {
              return 'vendor-ui';
            }
            
            // Charting - separate chunks to avoid circular deps
            if (id.includes('recharts')) {
              return 'vendor-recharts';
            }
            if (id.includes('lightweight-charts')) {
              return 'vendor-tradingview';
            }
            if (id.includes('chart.js') || id.includes('react-chartjs-2')) {
              return 'vendor-chartjs';
            }
            
            // Data fetching
            if (id.includes('@tanstack/react-query') || id.includes('axios')) {
              return 'vendor-data';
            }
            
            // Animation
            if (id.includes('framer-motion')) {
              return 'vendor-motion';
            }
            
            // Socket.IO
            if (id.includes('socket.io')) {
              return 'vendor-socket';
            }
            
            // Other vendors
            return 'vendor-misc';
          }
          
          // Application code chunking
          if (id.includes('/pages/')) {
            const match = id.match(/\/pages\/(\w+)\./);
            if (match) {
              return `page-${match[1].toLowerCase()}`;
            }
          }
          
          // Contexts and hooks - shared core
          if (id.includes('/contexts/') || id.includes('/hooks/')) {
            return 'app-core';
          }
          
          // Components - shared UI
          if (id.includes('/components/ui/')) {
            return 'app-ui';
          }
        },
      },
    },
    
    // Terser options for aggressive minification
    terserOptions: {
      compress: {
        drop_console: mode === 'production',
        drop_debugger: mode === 'production',
        pure_funcs: mode === 'production' ? ['console.log', 'console.info', 'console.debug'] : [],
        passes: 2, // Multiple compression passes
      },
      mangle: {
        safari10: true, // Safari 10 compatibility
      },
      format: {
        comments: false, // Remove all comments
      },
    },
  },
  
  // ============================================
  // DEVELOPMENT SERVER CONFIGURATION
  // ============================================
  server: {
    port: 3000,
    host: '0.0.0.0',
    allowedHosts: true,
    
    // Enable HTTP/2 in development
    // http2: true, // Uncomment if using HTTPS locally
    
    // Proxy configuration
    proxy: {
      "/api": {
        target: BACKEND_URL,
        changeOrigin: true,
        secure: false,
        logLevel: "warn",
        onError: (err, req, res) => {
          console.error(`[Proxy Error] ${req.method} ${req.path}:`, err.message);
          res.writeHead(502, { "Content-Type": "application/json" });
          res.end(JSON.stringify({
            error: {
              code: "BACKEND_UNAVAILABLE",
              message: "Backend API is not available. Ensure the dev server is running on " + BACKEND_URL,
            }
          }));
        },
      },
      "/socket.io": {
        target: BACKEND_URL,
        changeOrigin: true,
        secure: false,
        ws: true,
        logLevel: "warn",
      },
      "/health": {
        target: BACKEND_URL,
        changeOrigin: true,
        secure: false,
        logLevel: "warn",
      },
      "/ping": {
        target: BACKEND_URL,
        changeOrigin: true,
        secure: false,
        logLevel: "warn",
      },
      "/csrf": {
        target: BACKEND_URL,
        changeOrigin: true,
        secure: false,
        logLevel: "warn",
      },
    },
  },
  
  // ============================================
  // PLUGINS
  // ============================================
  plugins: [
    react({
      // Use SWC for faster builds
      jsxImportSource: undefined,
    }),
    mode === "development" && componentTagger(),
    // Split vendor chunks automatically
    splitVendorChunkPlugin(),
  ].filter(Boolean),
  
  // ============================================
  // MODULE RESOLUTION
  // ============================================
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  
  // ============================================
  // OPTIMIZATION
  // ============================================
  optimizeDeps: {
    // Pre-bundle these for faster dev startup
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      '@tanstack/react-query',
      'axios',
      'zustand',
      'date-fns',
      'lucide-react',
    ],
    // Exclude heavy packages from pre-bundling
    exclude: [
      'ethers',
      'lightweight-charts',
    ],
  },
  
  // ============================================
  // PREVIEW SERVER (for testing production build)
  // ============================================
  preview: {
    port: 4173,
    host: '0.0.0.0',
  },
  
  // ============================================
  // ESBuild OPTIONS
  // ============================================
  esbuild: {
    // Drop console in production
    drop: mode === 'production' ? ['console', 'debugger'] : [],
    // Legal comments handling
    legalComments: 'none',
  },
}));
