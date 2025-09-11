import js from '@eslint/js';
import globals from 'globals';
import tsParser from '@typescript-eslint/parser';
import pluginReact from 'eslint-plugin-react';
import { defineConfig } from 'eslint/config';
import pluginTs from '@typescript-eslint/eslint-plugin';
import json from '@eslint/json';

export default defineConfig([
    // 除外パターン（Flat Config は .eslintignore 非対応のためここで指定）
    {
        ignores: [
            'dist/**',
            'public/**',
            'node_modules/**',
            '*.config.{js,ts}',
            'vite.config.ts',
            'tsconfig*.json',
            'scripts/**',
            '__archive__/**',
        ],
    },
    // JS/TS/JSX/TSX 共通（アプリコードに限定）
    {
        files: ['src/**/*.{js,ts,jsx,tsx}'],
        languageOptions: {
            parser: tsParser,
            parserOptions: {
                ecmaVersion: 2020,
                sourceType: 'module',
                ecmaFeatures: { jsx: true },
            },
            globals: globals.browser,
        },
        plugins: {
            '@typescript-eslint': pluginTs,
            react: pluginReact,
        },
        rules: {
            ...pluginTs.configs.recommended.rules,
            ...pluginReact.configs.recommended.rules,
            '@typescript-eslint/consistent-type-imports': 'warn',
            // 暫定: any は段階的移行のため warn に緩和
            '@typescript-eslint/no-explicit-any': 'warn',
        },
    },
    // JSONファイル用
    {
        files: ['**/*.json'],
        extends: [json.configs.recommended],
    },
]);
