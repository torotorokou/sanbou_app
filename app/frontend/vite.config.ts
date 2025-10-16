import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import { fileURLToPath } from 'url';
import customMediaPlugin from './src/plugins/vite-plugin-custom-media';

// ESM 環境では __dirname が無いので定義
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export default defineConfig(({ mode }) => {
    // プロジェクトルートの env ディレクトリを指定
    const envDir = path.resolve(__dirname, '../../env');
    
    // Vite の loadEnv で環境変数を読み込む
    const env = loadEnv(mode, envDir, '');

    const DEV_PORT = Number(env.DEV_FRONTEND_PORT ?? 5173);
    const CORE_PORT = Number(env.DEV_CORE_API_PORT ?? 8003);

    return {
        envDir, // Vite に env ディレクトリを伝える
        plugins: [react(), customMediaPlugin()],
        resolve: {
            alias: {
                '@': path.resolve(__dirname, 'src'),
                '@/app': path.resolve(__dirname, 'src/app'),
                '@/shared': path.resolve(__dirname, 'src/shared'),
                '@/features': path.resolve(__dirname, 'src/features'),
                '@/pages': path.resolve(__dirname, 'src/pages'),
                // Backward compatibility (no slash)
                '@app': path.resolve(__dirname, 'src/app'),
                '@shared': path.resolve(__dirname, 'src/shared'),
                '@features': path.resolve(__dirname, 'src/features'),
                '@pages': path.resolve(__dirname, 'src/pages'),
            },
        },
        server: {
            host: '0.0.0.0',
            port: DEV_PORT,
            proxy: {
                // Core API handles all /api/** requests (BFF pattern)
                '/api': { target: `http://localhost:${CORE_PORT}`, changeOrigin: true },
            },
        },
    };
});
