# Sanbou App Frontend

## 概要
Sanbou Appは、レポート生成・データベース管理・マニュアル表示・AI質問応答などの機能を提供するフロントエンドアプリケーションです。

**技術スタック**:
- React 18.3 + TypeScript 5.8
- Vite 7.0 (ビルドツール)
- Ant Design 5.24 (UIライブラリ)
- Zustand (状態管理)
- React Router 7.0 (ルーティング)

---

## 🏗️ アーキテクチャ

### Feature-Sliced Design (FSD)
本プロジェクトは **Feature-Sliced Design** を採用しています。

```
src/
├── app/                    # アプリケーション初期化
├── pages/                  # ルートレベルページ
├── widgets/                # 複合コンポーネント (将来)
├── features/               # ビジネス機能
│   ├── notification/      # ✅ 完全移行済み
│   ├── report/            # 📝 Phase 4で移行予定
│   ├── database/          # 📝 Phase 4で移行予定
│   ├── manual/            # 📝 Phase 4で移行予定
│   └── chat/              # 📝 Phase 4で移行予定
├── entities/               # エンティティ (将来)
└── shared/                 # 共有インフラ・ユーティリティ
    ├── infrastructure/    # ✅ HTTP client
    ├── utils/             # ✅ 汎用関数
    ├── types/             # ✅ 共通型定義
    ├── hooks/ui/          # ✅ UIフック
    ├── ui/                # ✅ 汎用UIコンポーネント
    └── constants/         # ✅ 定数・設定
```

**詳細**: `ARCHITECTURE.md`

---

## 📚 主要機能

### 1. Report (レポート生成)
日報・月次レポート・年次レポートの生成・ダウンロード

- PDF/Excel出力
- CSVアップロード
- インタラクティブフロー (ブロック単価等)

**詳細**: `features/report/README.md`

### 2. Database (データベース管理)
CSVデータのアップロード・検証・プレビュー

- CSV検証ルール
- エラーハイライト
- データプレビュー

**詳細**: `features/database/README.md`

### 3. Manual (マニュアル表示)
階層マニュアルの表示・検索・目次ナビゲーション

- 全文検索
- 目次スクロール
- アンカーリンク

**詳細**: `features/manual/README.md`

### 4. Chat (AI質問応答)
RAGベースのAI質問応答システム

- 質問テンプレート
- ストリーム応答
- PDFプレビュー

**詳細**: `features/chat/README.md`

### 5. Notification (通知)
アプリケーション全体の通知システム (✅ FSD完全移行済み)

- Toast通知
- 通知センター
- Zustand状態管理

**詳細**: `features/notification/README.md`

---

## 🚀 開発環境セットアップ

### 前提条件
- Node.js 18+
- npm 9+

### インストール
```bash
# 依存関係インストール
npm install

# 開発サーバー起動 (http://localhost:5173)
npm run dev

# ビルド
npm run build

# ビルド結果プレビュー
npm run preview

# Lint
npm run lint
```

---

## 📖 ドキュメント

### アーキテクチャ関連
- `ARCHITECTURE.md` - 全体アーキテクチャガイド
- `MIGRATION_STATUS.md` - FSD移行進捗追跡
- `PHASE2_COMPLETION_REPORT.md` - Phase 2完了レポート
- `PHASE3_COMPLETION_REPORT.md` - Phase 3完了レポート

### 機能別ドキュメント
- `features/notification/README.md` - 通知機能
- `features/report/README.md` - レポート生成
- `features/database/README.md` - データベース管理
- `features/manual/README.md` - マニュアル表示
- `features/chat/README.md` - AI質問応答

---

## 🛠️ 開発ガイドライン

### Import Path Aliases
```typescript
// Features層
import { notifySuccess } from '@features/notification';

// Shared層
import { apiGet } from '@shared/infrastructure/http';
import { useWindowSize } from '@shared/hooks/ui';
import { ensureSectionAnchors } from '@shared/utils/anchors';

// Components層 (Phase 4移行まで)
import ReportBase from '@/components/Report/ReportBase';
```

### 新機能追加フロー
1. `features/[feature-name]/` ディレクトリ作成
2. `README.md` 作成 (責務・構造・使用例)
3. `index.ts` 公開API定義
4. 実装 (model/controller/view)
5. ドキュメント更新

**詳細**: `ARCHITECTURE.md` > 開発ガイドライン

---

## 📊 FSD移行ステータス

| Phase | ステータス | 完了日 | 概要 |
|-------|----------|--------|------|
| Phase 1 | ✅ 完了 | 2025-09-XX | ディレクトリ構造作成 |
| Phase 2 | ✅ 完了 | 2025-10-03 | Shared層インポートパス置換 (40ファイル) |
| Phase 3 | ✅ 完了 | 2025-10-03 | Features層ドキュメント整備 |
| Phase 4 | ⏳ 計画中 | TBD | Feature完全移行 (段階的) |
| Phase 5 | 📋 未着手 | TBD | Pages層整理 |
| Phase 6 | 📋 未着手 | TBD | 完全なFSD達成 |

**詳細**: `MIGRATION_STATUS.md`

---

## 🧪 テスト (Phase 6予定)

### ユニットテスト
```bash
npm run test
```

### E2Eテスト
```bash
npm run test:e2e
```

---

## 📝 ESLint設定

### 基本設定
```js
// eslint.config.js
export default tseslint.config([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...
      // Enable lint rules for React
      reactX.configs['recommended-typescript'],
      // Enable lint rules for React DOM
      reactDom.configs.recommended,
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```
