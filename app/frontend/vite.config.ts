import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import yaml from '@rollup/plugin-yaml'; // ← 追加
import { fileURLToPath } from 'url';

// ESM 環境では __dirname が無いので定義
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export default defineConfig({
    plugins: [
        react(),
        yaml(), // ← 追加
    ],
    resolve: {
        alias: {
            '@': path.resolve(__dirname, 'src'), // '@/...' -> <repo>/app/frontend/src
        },
    },
    server: {
        host: '0.0.0.0',
        port: 5173,
        proxy: {
            '/sql_api': {
                target: 'http://sql_api:8000',
                changeOrigin: true,
            },
            '/ai_api': {
                target: 'http://ai_api:8000',
                changeOrigin: true,
            },
            '/ledger_api': {
                target: 'http://ledger_api:8000',
                changeOrigin: true,
            },
            '/rag_api': {
                target: 'http://rag_api:8000',
                changeOrigin: true,
            },
            '/manual_api': {
                target: 'http://manual_api:8000',
                changeOrigin: true,
            },
        },
    },
});
