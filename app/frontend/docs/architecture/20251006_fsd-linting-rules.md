# FSD依存関係ルール - ESLint設定ドキュメント

## 概要
Feature-Sliced Design (FSD)アーキテクチャの依存関係ルールを強制するため、`eslint-plugin-boundaries`を使用してESLint設定を行いました。

## 依存関係ルール

FSDアーキテクチャでは、以下の順序でのみ依存が許可されます:

```
app → pages → widgets → features → entities → shared
```

### レイヤー別の依存可能範囲

- **app**: `pages`, `widgets`, `features`, `entities`, `shared` に依存可能
- **pages**: `widgets`, `features`, `entities`, `shared` に依存可能
- **widgets**: `features`, `entities`, `shared` に依存可能
- **features**: `entities`, `shared` に依存可能
- **entities**: `shared` のみに依存可能
- **shared**: どこにも依存不可（外部ライブラリのみ）

## 設定内容

### ESLint設定 (`eslint.config.js`)

```javascript
'boundaries/element-types': [
    'error',
    {
        default: 'disallow',
        message: '❌ FSD依存ルール違反: app→pages→widgets→features→entities→shared の順でしか依存できません',
        rules: [
            { from: ['app'], allow: ['pages', 'widgets', 'features', 'entities', 'shared'] },
            { from: ['pages'], allow: ['widgets', 'features', 'entities', 'shared'] },
            { from: ['widgets'], allow: ['features', 'entities', 'shared'] },
            { from: ['features'], allow: ['entities', 'shared'] },
            { from: ['entities'], allow: ['shared'] },
            { from: ['shared'], allow: [] },
        ],
    },
],
```

### NPMスクリプト

```json
{
  "lint": "eslint \"src/**/*.{ts,tsx,js,jsx}\"",
  "lint:fix": "eslint \"src/**/*.{ts,tsx,js,jsx}\" --fix"
}
```

## 使用方法

### リント実行
```bash
npm run lint
```

### 自動修正
```bash
npm run lint:fix
```

## 制限事項と注意点

### 1. TypeScriptパスエイリアスの検出制限
現在の`eslint-plugin-boundaries`設定は、以下のパターンで動作します:

✅ **検出可能**:
- 相対パスでの違反: `import { X } from '../../../features/xxx'`

⚠️ **検出制限**:
- TypeScriptパスエイリアス: `import { X } from '@features/xxx'`
  - パスエイリアス（`@app/`, `@features/`等）を使った場合、プラグインがレイヤーを正しく判別できない場合があります

### 2. 同じディレクトリ内のファイル
以下のインポートは常に許可されます:
- CSS: `import './styles.css'`
- 型定義: `import type { X } from './types'`
- JSON: `import data from './data.json'`

### 3. 外部ライブラリ
全てのレイヤーから外部ライブラリ（`react`, `antd`, `axios`等）のインポートは許可されます。

## 違反例と修正方法

### ❌ 違反: sharedからfeaturesへの依存
```typescript
// src/shared/utils/helper.ts
import { something } from '@features/analysis'; // NG
```

**修正方法**: 
- `helper.ts`を`features/analysis/utils/`に移動
- または、共通ロジックを`shared/utils/`に抽出し、`features`で使用

### ❌ 違反: featuresからpagesへの依存
```typescript
// src/features/dashboard/ui/Panel.tsx
import { SomePage } from '@pages/home'; // NG
```

**修正方法**:
- `Panel`コンポーネントを`pages/home/`に移動
- または、共通UIを`shared/ui/`に抽出

## CI/CDでの活用

```yaml
# .github/workflows/lint.yml
- name: Run ESLint
  run: npm run lint
```

## 今後の改善案

### オプション1: eslint-plugin-importの導入
TypeScriptパスエイリアスをより確実に検出するため、`eslint-plugin-import`と`import/no-restricted-paths`の併用を検討:

```bash
npm install --save-dev eslint-plugin-import eslint-import-resolver-typescript
```

### オプション2: マージ前チェック
Pull Request作成時に、自動的に`npm run lint`を実行するGitHub Actionsワークフローを追加。

## トラブルシューティング

### ESLintエラー: "boundaries/element-types"
設定ファイルの構文エラーです。`eslint.config.js`を確認してください。

### 違反が検出されない
1. パスエイリアス（`@features/`等）を使っている場合、検出されない可能性があります
2. 相対パス（`../../../features/`）で試してみてください
3. または、上記の「改善案」を参照して`eslint-plugin-import`の導入を検討してください

## 参考リンク
- [Feature-Sliced Design公式](https://feature-sliced.design/)
- [eslint-plugin-boundaries](https://github.com/javierbrea/eslint-plugin-boundaries)
- [ESLint Flat Config](https://eslint.org/docs/latest/use/configure/configuration-files-new)
