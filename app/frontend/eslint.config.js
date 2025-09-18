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
            'package.json',
            'package-lock.json',
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
        settings: {
            react: {
                version: 'detect',
            },
        },
        rules: {
            ...pluginTs.configs.recommended.rules,
            ...pluginReact.configs.recommended.rules,
            '@typescript-eslint/consistent-type-imports': 'warn',
            // 暫定: any は段階的移行のため warn に緩和
            '@typescript-eslint/no-explicit-any': 'warn',
        },
    },
    // ページ配下のみ、インラインstyleの危険プロパティを警告
    {
        files: ['src/pages/**/*.{js,ts,jsx,tsx}'],
        rules: {
            'no-restricted-syntax': [
                'warn',
                {
                    selector:
                        "JSXAttribute[name.name='style'] Property[key.name=/^(height|minHeight|maxHeight)$/]",
                    message: 'inline styleの高さ指定は禁止。Page/Layoutに集約してください。',
                },
                {
                    selector:
                        "JSXAttribute[name.name='style'] Property[key.name=/^(overflow|overflowY|overflowX)$/]",
                    message: 'inline styleのoverflowは禁止。本文1か所のみに統一してください。',
                },
                {
                    selector:
                        "JSXAttribute[name.name='style'] Literal[value=/vh/]",
                    message: 'inline styleでvh単位は使用禁止。必要時は骨格側の100dvhを使用。',
                },
            ],
        },
    },
    // JSONファイル用
    {
        files: ['**/*.json'],
        extends: [json.configs.recommended],
    },
]);
