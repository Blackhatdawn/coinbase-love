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
    outDir: 'build',
    minify: 'terser',
    sourcemap: mode !== 'production',
    target: 'ES2020',
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        manualChunks: (id) => {
          // Vendor chunk
          if (id.includes('node_modules')) {
            if (id.includes('ethers')) {
              return 'web3-vendor';
            }
            if (id.includes('@radix-ui') || id.includes('cmdk') || id.includes('sonner')) {
              return 'ui-vendor';
            }
            if (id.includes('recharts') || id.includes('lightweight-charts')) {
              return 'charts-vendor';
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
  },
  server: {
    port: 3000,
    host: '0.0.0.0',
    allowedHosts: true,
    proxy: mode === 'development' ? {
      "/api": {
        target: process.env.VITE_API_URL || "http://localhost:8001",
        changeOrigin: true,
        secure: false,
      },
    } : undefined,
  },
  plugins: [react(), mode === "development" && componentTagger()].filter(Boolean),
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
}));
