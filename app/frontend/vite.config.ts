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
    
    // 環境に応じたターゲットURL
    // Docker内で実行: サービス名を使用
    // ローカルで実行: localhost:8003を使用
    const isDockerEnvironment = process.env.DOCKER === 'true';
    const coreApiTarget = isDockerEnvironment 
        ? 'http://core_api:8000'
        : `http://localhost:${CORE_PORT}`;
    
    console.log(`[Vite] Docker environment: ${isDockerEnvironment}`);
    console.log(`[Vite] Core API target: ${coreApiTarget}`);

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
        // ビルド最適化設定
        build: {
            // 出力ディレクトリ
            outDir: 'dist',
            // ソースマップ（本番では無効化）
            sourcemap: mode !== 'production',
            // チャンク分割設定
            rollupOptions: {
                output: {
                    manualChunks: {
                        // ベンダーライブラリを分割
                        'vendor-react': ['react', 'react-dom', 'react-router-dom'],
                        'vendor-antd': ['antd', '@ant-design/icons'],
                        'vendor-charts': ['recharts'],
                    },
                },
            },
            // チャンクサイズ警告閾値
            chunkSizeWarningLimit: 1000,
        },
        server: {
            host: '0.0.0.0',
            port: DEV_PORT,
            proxy: {
                // BFF統一: /core_api リクエストを core_api サービスに転送
                '/core_api': {
                    target: coreApiTarget,
                    changeOrigin: true,
                    secure: false,
                },
                // Legacy support: /api/* も core_api に転送（互換性のため）
                '/api': { 
                    target: coreApiTarget, 
                    changeOrigin: true,
                    secure: false,
                    rewrite: (p) => p.replace(/^\/api/, '/core_api'),
                },
            },
        },
    };
});
