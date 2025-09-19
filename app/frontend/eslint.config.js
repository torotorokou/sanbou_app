import js from '@eslint/js';
import globals from 'globals';
import tsParser from '@typescript-eslint/parser';
import pluginReact from 'eslint-plugin-react';
import { defineConfig } from 'eslint/config';
import pluginTs from '@typescript-eslint/eslint-plugin';
import json from '@eslint/json';
import boundaries from 'eslint-plugin-boundaries';

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
            boundaries,
        },
        settings: {
            react: {
                version: 'detect',
            },
            'boundaries/elements': [
                { type: 'shared', pattern: 'src/shared/**', mode: 'full' },
                { type: 'domain', pattern: 'src/domain/**', mode: 'full' },
                { type: 'infra', pattern: 'src/infra/**', mode: 'full' },
                { type: 'controllers', pattern: 'src/controllers/**', mode: 'full' },
                { type: 'features', pattern: 'src/features/**', mode: 'full' },
            ],
        },
        rules: {
            ...pluginTs.configs.recommended.rules,
            ...pluginReact.configs.recommended.rules,
            '@typescript-eslint/consistent-type-imports': 'warn',
            // 暫定: any は段階的移行のため warn に緩和
            '@typescript-eslint/no-explicit-any': 'warn',
            'boundaries/element-types': [
                'error',
                {
                    default: 'disallow',
                    message: '依存の向きを守ってください。',
                    rules: [
                        { from: ['features'], allow: ['shared', 'controllers'] },
                        { from: ['controllers'], allow: ['shared', 'domain'] },
                        { from: ['domain'], allow: ['shared'] },
                        { from: ['infra'], allow: ['shared', 'domain'] },
                    ],
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
