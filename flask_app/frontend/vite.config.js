// JP: Vite のビルド/開発サーバー設定
// EN: Vite build and dev server configuration
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  // JP: React プラグインを利用
  // EN: Enable React plugin
  plugins: [react()],
  build: {
    // JP: 出力先は FastAPI の静的ディレクトリ
    // EN: Output into FastAPI static directory
    outDir: '../static/dist_vite',
    emptyOutDir: true,
    rollupOptions: {
      input: {
        // JP: 複数エントリ（メイン/ WebArena/ 結果画面）
        // EN: Multiple entry points (main/WebArena/result)
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
    // JP: 開発時は FastAPI にプロキシ
    // EN: Proxy API calls to FastAPI during dev
    proxy: {
      '/api': 'http://localhost:5005',
      '/webarena': 'http://localhost:5005',
      '/model_settings': 'http://localhost:5005',
      '/favicon.png': 'http://localhost:5005',
      '/favicon.ico': 'http://localhost:5005',
    },
  },
});
