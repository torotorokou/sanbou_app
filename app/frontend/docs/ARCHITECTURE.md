# Sanbou App Frontend Architecture

## アーキテクチャ原則

### Feature-Sliced Design (FSD) の採用
本プロジェクトは **Feature-Sliced Design** を基盤としたアーキテクチャを採用しています。

### レイヤー構造
```
app/frontend/src/
├── app/                    # アプリケーション初期化
├── pages/                  # ルートレベルページ
├── widgets/                # ページを構成する複合コンポーネント (将来)
├── features/               # ビジネス機能
│   ├── notification/      # ✅ 完全移行済み
│   ├── report/            # 📝 文書化済み (Phase 3)
│   ├── database/          # 📝 文書化済み (Phase 3)
│   ├── manual/            # 📝 文書化済み (Phase 3)
│   └── chat/              # 📝 文書化済み (Phase 3)
├── entities/               # ビジネスエンティティ (将来)
└── shared/                 # 共有インフラ・ユーティリティ
    ├── infrastructure/    # ✅ HTTP client
    ├── utils/             # ✅ 汎用関数
    ├── types/             # ✅ 共通型定義
    ├── hooks/ui/          # ✅ UIフック
    ├── ui/                # ✅ 汎用UIコンポーネント
    └── constants/         # ✅ 定数・設定
```

---

## 現在のアーキテクチャ (Phase 3完了時点)

### レイヤー別詳細

#### 1. App層 (`app/`)
**責務**: アプリケーションの初期化とグローバル設定

```
app/
├── App.tsx                # ルートコンポーネント
└── main.tsx               # エントリーポイント
```

**主要機能**:
- React Router初期化
- テーマプロバイダー
- 認証コンテキスト

---

#### 2. Pages層 (`pages/`)
**責務**: ルーティング可能なページコンポーネント

```
pages/
├── home/                  # ポータルページ
├── report/                # レポート管理ページ
├── manual/                # マニュアルページ
├── database/              # データベース管理ページ
├── navi/                  # AI質問応答ページ
├── analysis/              # データ分析ページ
└── dashboard/             # ダッシュボードページ
```

**特徴**:
- ルーティング定義と対応
- ページレベルの状態管理
- 複数のfeaturesを組み合わせ

---

#### 3. Features層 (`features/`)
**責務**: ビジネス機能の実装

##### ✅ notification (完全移行済み)
```
features/notification/
├── model/                 # 型定義・ストア
│   ├── notification.types.ts
│   └── notification.store.ts
├── controller/            # ビジネスロジック
│   └── notify.ts
├── view/                  # UIコンポーネント
│   ├── NotificationCenter.tsx
│   └── NotificationCenterAntd.tsx
├── config.ts              # 設定
├── index.ts               # 公開API
└── README.md              # ドキュメント
```

**公開API**:
```typescript
// 推奨: 名前付きエクスポート
export { useNotificationStore } from './model/notification.store';
export { notifySuccess, notifyError, notifyInfo, notifyWarning } from './controller/notify';
export { NotificationCenter, NotificationCenterAntd } from './view';
```

##### 📝 report (文書化済み、Phase 4で移行予定)
**現在の配置**:
- Components: `src/components/Report/`
- Hooks: `src/hooks/report/`
- Types: `src/types/reportBase.ts`
- Config: `src/constants/reportConfig.ts`

**主要機能**:
- レポート生成 (PDF/Excel)
- CSVアップロード
- インタラクティブフロー
- プレビュー

**詳細**: `features/report/README.md`

##### 📝 database (文書化済み、Phase 4で移行予定)
**現在の配置**:
- Components: `src/components/database/`, `src/components/common/csv-upload/`
- Hooks: `src/hooks/database/`

**主要機能**:
- CSVアップロード
- データ検証
- プレビュー

**詳細**: `features/database/README.md`

##### 📝 manual (文書化済み、Phase 4で移行予定)
**現在の配置**:
- Components: `src/components/manual/`
- API: `src/services/api/manualsApi.ts`
- Types: `src/types/manuals.ts`

**主要機能**:
- マニュアル表示
- 検索
- 目次ナビゲーション

**詳細**: `features/manual/README.md`

##### 📝 chat (文書化済み、Phase 4で移行予定)
**現在の配置**:
- Components: `src/components/chat/`
- API: `src/services/chatService.ts`

**主要機能**:
- AI質問応答
- PDFプレビュー
- 質問テンプレート

**詳細**: `features/chat/README.md`

---

#### 4. Shared層 (`shared/`)
**責務**: 横断的な共有機能

##### ✅ Infrastructure (`shared/infrastructure/`)
```
infrastructure/
└── http/                  # HTTP client
    ├── httpClient.ts      # 公開API
    ├── httpClient_impl.ts # 実装
    └── index.ts
```

**提供機能**:
- `apiGet()`, `apiPost()`, `apiGetBlob()`, `apiPostBlob()`
- 統一エラーハンドリング
- API envelope パース

##### ✅ Utils (`shared/utils/`)
```
utils/
├── anchors.ts             # TOC生成・スクロール
├── pdfWorkerLoader.ts     # PDF.js遅延ロード
├── responsiveTest.ts      # レスポンシブテスト
├── csv/
│   └── csvPreview.ts      # CSVプレビュー
└── validators/
    └── csvValidator.ts    # CSV検証
```

##### ✅ Types (`shared/types/`)
```
types/
├── api.ts                 # ApiResponse型
└── yaml.d.ts              # YAML型定義
```

##### ✅ Hooks/UI (`shared/hooks/ui/`)
```
hooks/ui/
├── useWindowSize.ts       # ウィンドウサイズ
├── useResponsive.ts       # レスポンシブ判定
├── useContainerSize.ts    # コンテナサイズ
├── useScrollTracker.ts    # スクロール追跡
├── useSidebarDefault.ts   # サイドバー状態
├── useSidebarResponsive.ts
└── index.ts
```

##### ✅ UI Components (`shared/ui/`)
```
ui/
├── AnimatedStatistic.tsx
├── DiffIndicator.tsx
├── ReportStepIndicator.tsx
├── StatisticCard.tsx
├── TrendChart.tsx
├── TypewriterText.tsx
├── VerticalActionButton.tsx
├── DownloadButton.tsx
└── index.ts
```

---

## Import Path Aliases

### 設定済みエイリアス
```typescript
{
  "@/*": ["./src/*"],
  "@features/*": ["./src/features/*"],
  "@shared/*": ["./src/shared/*"],
  "@app/*": ["./src/app/*"],
  "@pages/*": ["./src/pages/*"],
  "@widgets/*": ["./src/widgets/*"],
  "@components/*": ["./src/components/*"],
  "@hooks/*": ["./src/hooks/*"],
  "@stores/*": ["./src/stores/*"],
  "@types/*": ["./src/types/*"],
  "@utils/*": ["./src/utils/*"],
  "@config/*": ["./src/config/*"],
  "@constants/*": ["./src/constants/*"],
  "@layout/*": ["./src/layout/*"],
  "@theme/*": ["./src/theme/*"],
  "@services/*": ["./src/services/*"],
  "@entities/*": ["./src/entities/*"],
  "@domain/*": ["./src/domain/*"],
  "@infra/*": ["./src/infra/*"],
  "@controllers/*": ["./src/controllers/*"]
}
```

### 推奨インポートパターン

#### Features層
```typescript
// ✅ 良い例: 名前付きインポート + 公開API
import { useNotificationStore, notifySuccess } from '@features/notification';

// ❌ 悪い例: 内部実装に直接アクセス
import { useNotificationStore } from '@features/notification/model/notification.store';
```

#### Shared層
```typescript
// ✅ 良い例: カテゴリ別インポート
import { apiGet, apiPost } from '@shared/infrastructure/http';
import { useWindowSize, useResponsive } from '@shared/hooks/ui';
import { ensureSectionAnchors } from '@shared/utils/anchors';

// ❌ 悪い例: 深いパス
import { apiGet } from '@shared/infrastructure/http/httpClient_impl';
```

#### Components層 (Phase 4移行まで)
```typescript
// ✅ 現在の推奨
import ReportBase from '@/components/Report/ReportBase';
import { useReportManager } from '@/hooks/report';

// ✅ Phase 4以降
import { ReportBase, useReportManager } from '@features/report';
```

---

## 依存関係ルール

### レイヤー間の依存方向
```
app → pages → widgets → features → entities → shared
```

**許可**:
- 上位レイヤーは下位レイヤーに依存OK
- 同一レイヤー内のfeature間は **依存禁止** (独立性維持)

**禁止**:
- 下位レイヤーが上位レイヤーに依存
- shared → features への依存
- features → pages への依存

### Feature間通信

#### ❌ 直接依存 (禁止)
```typescript
// features/report/
import { notifySuccess } from '../notification/controller/notify';  // NG
```

#### ✅ 公開API経由 (推奨)
```typescript
// features/report/
import { notifySuccess } from '@features/notification';  // OK
```

#### ✅ イベントバス (将来)
```typescript
// features/report/
eventBus.emit('report:generated', { reportId });

// features/notification/
eventBus.on('report:generated', ({ reportId }) => {
  notifySuccess('レポート生成完了');
});
```

---

## 状態管理

### Zustand Store (推奨)
- グローバル状態: Zustandストア (`features/*/model/*.store.ts`)
- ローカル状態: React useState

### Store配置ルール
```
features/[feature]/
└── model/
    ├── [feature].types.ts   # 型定義
    └── [feature].store.ts   # Zustand store
```

### 例: Notification Store
```typescript
// features/notification/model/notification.store.ts
import { create } from 'zustand';

export const useNotificationStore = create<NotificationState>((set) => ({
  notifications: [],
  addNotification: (notification) => set((state) => ({
    notifications: [...state.notifications, notification]
  })),
  removeNotification: (id) => set((state) => ({
    notifications: state.notifications.filter(n => n.id !== id)
  }))
}));
```

---

## コンポーネント設計

### UIコンポーネント分類

#### Shared UI (`shared/ui/`)
- **特徴**: ビジネスロジックなし、完全に汎用的
- **例**: Button, Card, Modal, AnimatedStatistic
- **Props**: すべて外部から注入

#### Feature UI (`features/*/ui/`)
- **特徴**: 特定機能に特化
- **例**: ReportBase, ChatQuestionSection
- **Props**: 機能固有のデータ構造

#### Page Components (`pages/`)
- **特徴**: ルーティング可能、複数featureを組み合わせ
- **例**: ReportFactory, SolvestNavi
- **Props**: URLパラメータから取得

---

## TypeScript 型管理

### 型定義の配置

#### 共有型 (`shared/types/`)
```typescript
// shared/types/api.ts
export type ApiResponse<T = unknown> = {
  status: 'success' | 'error';
  data?: T;
  detail?: string;
};
```

#### Feature型 (`features/*/model/`)
```typescript
// features/notification/model/notification.types.ts
export type Notification = {
  id: string;
  type: 'success' | 'error' | 'info' | 'warning';
  message: string;
  description?: string;
  duration?: number;
};
```

#### ドメイン型 (`@/types/`)
現状は移行中、Phase 4以降で `features/*/model/` に集約予定

---

## ビルドとバンドル

### Vite設定
- **ビルドツール**: Vite 7.0.0
- **ターゲット**: ES2020
- **コード分割**: 自動 (dynamic import)
- **最適化**: Tree shaking, Minification

### バンドルサイズ最適化
- 動的インポート: PDF.js, Chart.js
- Lazy Loading: ページコンポーネント
- Code Splitting: features単位

---

## テスト戦略 (将来)

### ユニットテスト
- **対象**: Business logic hooks, Utils
- **ツール**: Vitest
- **配置**: `*.test.ts` (同階層)

### 統合テスト
- **対象**: Feature全体
- **ツール**: React Testing Library
- **配置**: `features/*/tests/`

### E2Eテスト
- **対象**: ユーザーフロー
- **ツール**: Playwright
- **配置**: `e2e/`

---

## パフォーマンス

### 最適化施策
1. **コード分割**: features単位でchunk分離
2. **遅延読み込み**: PDF.js, Chart.js
3. **メモ化**: useMemo, useCallback, React.memo
4. **仮想化**: 大量データ表示 (react-window)

### メトリクス目標
- FCP (First Contentful Paint): < 1.5s
- LCP (Largest Contentful Paint): < 2.5s
- TTI (Time to Interactive): < 3.5s
- Bundle Size: Main chunk < 500KB

---

## セキュリティ

### XSS対策
- DOMPurify: HTMLサニタイズ
- CSP: Content Security Policy設定

### 認証/認可
- JWT Token: ローカルストレージ保存
- API通信: Authorization header

### CSRF対策
- CSRF Token: API通信に含める
- SameSite Cookie: 設定

---

## 開発ガイドライン

### 新機能追加フロー

#### Step 1: Feature作成
```bash
mkdir -p src/features/[feature-name]/{model,controller,view}
```

#### Step 2: README作成
```markdown
# [Feature Name]

## 概要
## 責務
## 構造
## 使用例
```

#### Step 3: 公開API定義
```typescript
// features/[feature-name]/index.ts
export { ... } from './model';
export { ... } from './controller';
export { ... } from './view';
```

#### Step 4: 実装
- model: 型定義・ストア
- controller: ビジネスロジック
- view: UIコンポーネント

#### Step 5: ドキュメント更新
- README.md
- ARCHITECTURE.md (本ファイル)

---

## 関連ドキュメント
- `PHASE2_COMPLETION_REPORT.md` - Phase 2完了レポート
- `PHASE3_SIMPLIFIED.md` - Phase 3簡略版計画
- `features/*/README.md` - 各Feature詳細
- `shared/README.md` - Shared層詳細

---

**最終更新**: 2025年10月3日  
**アーキテクチャバージョン**: 1.0 (Phase 3完了時点)  
**メンテナ**: Sanbou App Team
