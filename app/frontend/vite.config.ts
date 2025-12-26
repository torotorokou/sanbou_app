import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";
import { fileURLToPath } from "url";
import customMediaPlugin from "./src/plugins/vite-plugin-custom-media";
import { visualizer } from "rollup-plugin-visualizer";

// ESM 環境では __dirname が無いので定義
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export default defineConfig(({ mode }) => {
  // プロジェクトルートの env ディレクトリを指定
  const envDir = path.resolve(__dirname, "../../env");

  // Vite の loadEnv で環境変数を読み込む
  const env = loadEnv(mode, envDir, "");

  const DEV_PORT = Number(env.DEV_FRONTEND_PORT ?? 5173);
  const CORE_PORT = Number(env.DEV_CORE_API_PORT ?? 8003);

  // 環境に応じたターゲットURL
  // Docker内で実行: サービス名を使用
  // ローカルで実行: localhost:8003を使用
  const isDockerEnvironment = process.env.DOCKER === "true";
  const coreApiTarget = isDockerEnvironment
    ? "http://core_api:8000"
    : `http://localhost:${CORE_PORT}`;

  console.log(`[Vite] Docker environment: ${isDockerEnvironment}`);
  console.log(`[Vite] Core API target: ${coreApiTarget}`);

  return {
    envDir, // Vite に env ディレクトリを伝える
    plugins: [
      react(),
      customMediaPlugin(),
      visualizer({
        filename: "./dist/stats.html",
        open: false,
        gzipSize: true,
        brotliSize: true,
      }),
    ],
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "src"),
        "@/app": path.resolve(__dirname, "src/app"),
        "@/shared": path.resolve(__dirname, "src/shared"),
        "@/features": path.resolve(__dirname, "src/features"),
        "@/pages": path.resolve(__dirname, "src/pages"),
        // Backward compatibility (no slash)
        "@app": path.resolve(__dirname, "src/app"),
        "@shared": path.resolve(__dirname, "src/shared"),
        "@features": path.resolve(__dirname, "src/features"),
        "@pages": path.resolve(__dirname, "src/pages"),
      },
    },
    // ビルド最適化設定
    build: {
      // 出力ディレクトリ
      outDir: "dist",
      // ソースマップ（本番では無効化）
      sourcemap: mode !== "production",
      // チャンク分割設定
      rollupOptions: {
        output: {
          manualChunks: (id) => {
            // Node modules の分類
            if (id.includes("node_modules")) {
              // 1. React系は初回必須なので vendor-react にまとめる
              if (
                id.includes("react") ||
                id.includes("react-dom") ||
                id.includes("react-router")
              ) {
                return "vendor-react";
              }

              // 2. Ant Design は使用頻度が高いので vendor-antd
              if (id.includes("antd") || id.includes("@ant-design")) {
                return "vendor-antd";
              }

              // 3. recharts は遅延読み込みページでのみ使用（独立chunk）
              if (id.includes("recharts")) {
                return "vendor-charts";
              }

              // 4. 地図関連も遅延読み込みページでのみ使用（独立chunk）
              if (id.includes("leaflet") || id.includes("react-leaflet")) {
                return "vendor-map";
              }

              // 5. PDF関連も遅延読み込みページでのみ使用（独立chunk）
              if (
                id.includes("pdfjs-dist") ||
                id.includes("react-pdf") ||
                id.includes("canvas")
              ) {
                return "vendor-pdf";
              }

              // 6. dayjs（日時ライブラリ）
              if (id.includes("dayjs")) {
                return "vendor-dayjs";
              }

              // 7. axios（HTTP通信）
              if (id.includes("axios")) {
                return "vendor-axios";
              }

              // 8. zustand（状態管理）
              if (id.includes("zustand")) {
                return "vendor-zustand";
              }

              // 9. テーブル関連
              if (id.includes("@tanstack/react-table")) {
                return "vendor-table";
              }

              // 10. マークダウン関連
              if (
                id.includes("react-markdown") ||
                id.includes("remark") ||
                id.includes("rehype")
              ) {
                return "vendor-markdown";
              }

              // 11. その他のutilityライブラリ（jszip, papaparse等）
              if (id.includes("jszip") || id.includes("papaparse")) {
                return "vendor-utils";
              }

              // 12. その他のnode_modulesは vendor-misc へ
              return "vendor-misc";
            }
          },
        },
      },
      // チャンクサイズ警告閾値
      chunkSizeWarningLimit: 1000,
    },
    server: {
      host: "0.0.0.0",
      port: DEV_PORT,
      proxy: {
        // BFF統一: /core_api リクエストを core_api サービスに転送
        "/core_api": {
          target: coreApiTarget,
          changeOrigin: true,
          secure: false,
        },
        // Legacy support: /api/* も core_api に転送（互換性のため）
        "/api": {
          target: coreApiTarget,
          changeOrigin: true,
          secure: false,
          rewrite: (p) => p.replace(/^\/api/, "/core_api"),
        },
      },
    },
  };
});
