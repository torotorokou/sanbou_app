import js from "@eslint/js";
import globals from "globals";
import tsParser from "@typescript-eslint/parser";
import pluginReact from "eslint-plugin-react";
import { defineConfig } from "eslint/config";
import pluginTs from "@typescript-eslint/eslint-plugin";
import json from "@eslint/json";
import boundaries from "eslint-plugin-boundaries";
import eslintConfigPrettier from "eslint-config-prettier";

export default defineConfig([
  // 除外パターン（Flat Config は .eslintignore 非対応のためここで指定）
  {
    ignores: [
      "dist/**",
      "public/**",
      "node_modules/**",
      "src/theme/**",
      "*.config.{js,ts}",
      "vite.config.ts",
      "tsconfig*.json",
      "scripts/**",
      "package.json",
      "package-lock.json",
      "**/*.css",
      "**/*.scss",
      "**/*.less",
    ],
  },
  // JS/TS/JSX/TSX 共通（アプリコードに限定）
  {
    files: ["src/**/*.{js,ts,jsx,tsx}"],
    languageOptions: {
      parser: tsParser,
      parserOptions: {
        ecmaVersion: 2020,
        sourceType: "module",
        ecmaFeatures: { jsx: true },
      },
      globals: globals.browser,
    },
    plugins: {
      "@typescript-eslint": pluginTs,
      react: pluginReact,
      boundaries,
    },
    settings: {
      react: {
        version: "detect",
      },
      "boundaries/elements": [
        { type: "app", pattern: ["src/app/**", "app/**", "@app/**"] },
        { type: "pages", pattern: ["src/pages/**", "pages/**", "@pages/**"] },
        {
          type: "widgets",
          pattern: ["src/widgets/**", "widgets/**", "@widgets/**"],
        },
        {
          type: "features",
          pattern: ["src/features/**", "features/**", "@features/**"],
        },
        {
          type: "entities",
          pattern: ["src/entities/**", "entities/**", "@entities/**"],
        },
        {
          type: "shared",
          pattern: ["src/shared/**", "shared/**", "@shared/**"],
        },
      ],
    },
    rules: {
      ...pluginTs.configs.recommended.rules,
      ...pluginReact.configs.recommended.rules,
      "@typescript-eslint/consistent-type-imports": "warn",
      // React 17+ では React インポート不要
      "react/react-in-jsx-scope": "off",
      // TypeScript で型定義されているため prop-types は不要
      "react/prop-types": "off",
      // 暫定: any は段階的移行のため warn に緩和
      "@typescript-eslint/no-explicit-any": "warn",
      // ブレークポイントのマジックナンバー混入防止（比較演算子の文脈に限定）
      // NOTE: setTimeout等の無関係なリテラルやサンプルデータは誤検知しない
      // 5段階システム（xs/sm/md/lg/xl）を採用: 640/768/1024/1280
      "no-restricted-syntax": [
        "error",
        // 正規ブレークポイント（767/768/1199/1200）
        {
          selector:
            "BinaryExpression:matches([operator='<'],[operator='<='],[operator='>'],[operator='>=']):has(Literal[value=767])",
          message:
            "767 を比較に直書きせず、BP.mobileMax または述語関数を使用してください。",
        },
        {
          selector:
            "BinaryExpression:matches([operator='<'],[operator='<='],[operator='>'],[operator='>=']):has(Literal[value=768])",
          message:
            "768 を比較に直書きせず、BP.tabletMin または述語関数を使用してください。",
        },
        {
          selector:
            "BinaryExpression:matches([operator='<'],[operator='<='],[operator='>'],[operator='>=']):has(Literal[value=1199])",
          message:
            "1199 を比較に直書きせず、BP.desktopMin - 1 または述語関数を使用してください。",
        },
        {
          selector:
            "BinaryExpression:matches([operator='<'],[operator='<='],[operator='>'],[operator='>=']):has(Literal[value=1200])",
          message:
            "1200 を比較に直書きせず、BP.desktopMin または述語関数を使用してください。",
        },
      ],
      // shared層からの深いimport禁止（バレル公開強制）
      "no-restricted-imports": [
        "error",
        {
          patterns: [
            {
              group: ["@/shared/*/*/*", "@shared/*/*/*", "shared/*/*/*"],
              message:
                "❌ @/shared の深いimportは禁止です。@/shared からのみimportしてください（バレル公開）。",
            },
            {
              group: ["@/shared/*/*", "@shared/*/*", "shared/*/*"],
              message:
                "❌ @/shared の深いimportは禁止です。@/shared からのみimportしてください（バレル公開）。",
            },
          ],
        },
      ],
      "boundaries/element-types": [
        "error",
        {
          default: "disallow",
          message:
            "❌ FSD依存ルール違反: app→pages→widgets→features→entities→shared の順でしか依存できません",
          rules: [
            // app は全てのレイヤーに依存可能
            {
              from: ["app"],
              allow: ["pages", "widgets", "features", "entities", "shared"],
            },
            // pages は widgets/features/entities/shared に依存可能
            {
              from: ["pages"],
              allow: ["widgets", "features", "entities", "shared"],
            },
            // widgets は features/entities/shared に依存可能
            {
              from: ["widgets"],
              allow: ["features", "entities", "shared"],
            },
            // features は entities/shared に依存可能
            {
              from: ["features"],
              allow: ["entities", "shared"],
            },
            // entities は shared にのみ依存可能
            {
              from: ["entities"],
              allow: ["shared"],
            },
            // shared はどこにも依存不可（外部ライブラリのみ）
            {
              from: ["shared"],
              allow: [],
            },
          ],
        },
      ],
      // 同じディレクトリ内の相対インポート（./）は許可
      "boundaries/no-private": "off",
    },
  },
  // JSONファイル用
  {
    files: ["**/*.json"],
    extends: [json.configs.recommended],
  },
  // 例外許容: ブレークポイントの定義/ドキュメント/テスト
  {
    files: [
      "src/shared/constants/breakpoints.ts",
      "src/theme/cssVars.ts",
      "src/shared/styles/custom-media.css",
      "src/shared/constants/tests/**",
    ],
    rules: {
      "no-restricted-syntax": "off",
    },
  },
  // Prettier競合回避（最後に配置）
  eslintConfigPrettier,
]);
