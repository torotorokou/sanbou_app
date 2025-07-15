import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
    plugins: [react()],
    resolve: {
        alias: {
            '@': path.resolve(__dirname, 'src'),
        },
    },
    server: {
        host: '0.0.0.0', // ✅ 他コンテナからのアクセス許可
        port: 5173,
        proxy: {
            '/api/ai': {
                target: 'http://ai_api:8000',
                changeOrigin: true,
                // rewrite: path => path.replace(/^\/api\/ai/, '/api/ai') ← 明示不要
            },
            '/api/ledger': {
                target: 'http://ledger_api:8000',
                changeOrigin: true,
            },
        },
    },
});
