import js from '@eslint/js';
import globals from 'globals';
import tsParser from '@typescript-eslint/parser';
import pluginReact from 'eslint-plugin-react';
import { defineConfig } from 'eslint/config';
import pluginTs from '@typescript-eslint/eslint-plugin';
import json from '@eslint/json';

export default defineConfig([
    // JS/TS/JSX/TSX 共通
    {
        files: ['**/*.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'],
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
        },
        // extends: [js.configs.recommended], ← 明示的にextendsも不要
    },

    // JSONファイル用
    {
        files: ['**/*.json'],
        // parser: json.parsers['json'], ← これ不要・消す
        // plugins: { json }, ← これも不要・消す
        extends: [json.configs.recommended], // これだけでOK
    },
]);
