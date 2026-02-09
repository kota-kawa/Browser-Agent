import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: '../static/dist_vite',
    emptyOutDir: true,
    rollupOptions: {
      input: {
        index: path.resolve(__dirname, 'src/index.tsx'),
        webarena: path.resolve(__dirname, 'src/webarena.tsx'),
        agent_result: path.resolve(__dirname, 'src/agent_result.tsx'),
      },
      output: {
        entryFileNames: '[name].js',
        chunkFileNames: 'chunks/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash][extname]',
      },
    },
  },
  server: {
    proxy: {
      '/api': 'http://localhost:5005',
      '/webarena': 'http://localhost:5005',
      '/model_settings': 'http://localhost:5005',
      '/favicon.png': 'http://localhost:5005',
      '/favicon.ico': 'http://localhost:5005',
    },
  },
});
