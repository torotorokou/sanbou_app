import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import yaml from '@rollup/plugin-yaml'; // ← 追加
import { fileURLToPath } from 'url';

// ESM 環境では __dirname が無いので定義
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, process.cwd(), '');
    const useLocal = env.USE_LOCAL_BACKEND === '1';

    const targetFor = (service: string, localPort: number) =>
        useLocal ? `http://localhost:${localPort}` : `http://${service}:8000`;

    return {
        plugins: [react(), yaml()],
        resolve: {
            alias: {
                '@': path.resolve(__dirname, 'src'),
            },
        },
        server: {
            host: '0.0.0.0',
            port: 5173,
            proxy: {
                '/sql_api': { target: targetFor('sql_api', 8003), changeOrigin: true },
                '/ai_api': { target: targetFor('ai_api', 8001), changeOrigin: true },
                '/ledger_api': { target: targetFor('ledger_api', 8002), changeOrigin: true },
                '/rag_api': { target: targetFor('rag_api', 8004), changeOrigin: true },
                '/manual_api': { target: targetFor('manual_api', 8005), changeOrigin: true },
            },
        },
    };
});
