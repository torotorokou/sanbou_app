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
            '/api/ledger': {
                target: 'http://ledger_api:8000',
                changeOrigin: true,
            },
            // '/api/sql': は不要になるので削除してOK
        },
    },
});
