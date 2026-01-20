import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { componentTagger } from "lovable-tagger";

// https://vitejs.dev/config/
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
    proxy: {
      "/api": {
        target: "http://localhost:8000",
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
  }),
}));
