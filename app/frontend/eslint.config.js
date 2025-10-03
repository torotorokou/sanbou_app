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
                'src/theme/**',
            '*.config.{js,ts}',
            'vite.config.ts',
            'tsconfig*.json',
            'scripts/**',
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
            // ブレークポイントのマジックナンバー混入防止（比較演算子の文脈に限定）
            // NOTE: setTimeout等の無関係なリテラルやサンプルデータは誤検知しない
            'no-restricted-syntax': [
                'error',
                {
                    selector:
                        "BinaryExpression:matches([operator='<'],[operator='<='],[operator='>'],[operator='>=']):has(Literal[value=767])",
                    message:
                        '767 を比較に直書きせず、ANT.md - 1 または述語関数を使用してください。',
                },
                {
                    selector:
                        "BinaryExpression:matches([operator='<'],[operator='<='],[operator='>'],[operator='>=']):has(Literal[value=768])",
                    message:
                        '768 を比較に直書きせず、ANT.md または述語関数を使用してください。',
                },
                {
                    selector:
                        "BinaryExpression:matches([operator='<'],[operator='<='],[operator='>'],[operator='>=']):has(Literal[value=1199])",
                    message:
                        '1199 を比較に直書きせず、ANT.xl - 1 または述語関数を使用してください。',
                },
                {
                    selector:
                        "BinaryExpression:matches([operator='<'],[operator='<='],[operator='>'],[operator='>=']):has(Literal[value=1200])",
                    message:
                        '1200 を比較に直書きせず、ANT.xl または述語関数を使用してください。',
                },
            ],
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
    // 例外許容: ブレークポイントの定義/ドキュメント/テスト
    {
        files: [
            'src/shared/constants/breakpoints.ts',
            'src/theme/cssVars.ts',
            'src/theme/responsive.css',
            'src/shared/constants/tests/**',
        ],
        rules: {
            'no-restricted-syntax': 'off',
        },
    },
]);
