# Phase 6: Component Layer Cleanup - Planning Document

**作成日**: 2025-10-03  
**目的**: 残存コンポーネントを整理し、適切な層（Shared/Features）に移行

## 📊 現状分析

### 残存コンポーネント構造

```
src/components/
├── ManagementDashboard/     # 6 files - Dashboard feature用
├── Report/                  # 1 file - ReportBase.tsx (移行済み機能への依存)
├── TokenPreview/            # 1 file - Utils/Debug用
├── Utils/                   # 1 file - AnimatedStatistic.tsx
├── analysis/                # 0 files (空ディレクトリ)
├── common/                  # 0 files (空ディレクトリ)
├── debug/                   # 1 file - ResponsiveDebugInfo.tsx
├── examples/                # 1 file - CorrectApiUsageExample.tsx
├── rag/                     # 1 file - References.tsx
└── ui/                      # 8 files - 汎用UIコンポーネント
```

**合計**: 20ファイル（空ディレクトリ除く）

### components/ui/ の詳細 (8 files)

| ファイル | 用途 | 使用箇所 |
|---------|------|---------|
| `AnimatedStatistic.tsx` | アニメーション付き統計表示 | Dashboard系 |
| `DiffIndicator.tsx` | 差分インジケーター | Dashboard系 |
| `DownloadButton_.tsx` | ダウンロードボタン | Report系 |
| `ReportStepIndicator.tsx` | レポートステップ表示 | ChatPage, Report系 |
| `StatisticCard.tsx` | 統計カード | Dashboard系 |
| `TrendChart.tsx` | トレンドチャート | Dashboard系 |
| `TypewriterText.tsx` | タイプライター効果テキスト | ChatMessageCard |
| `VerticalActionButton.tsx` | 縦配置アクションボタン | Chat, Report |

### 使用状況分析

```
TypewriterText: 1箇所 (ChatMessageCard)
ReportStepIndicator: 2箇所 (ChatPage)
VerticalActionButton: 3箇所 (ChatSendButtonSection, ActionsSection x2)
```

## 🎯 Phase 6の戦略

### 目標
1. 汎用UIコンポーネントを`@shared/ui`に移行
2. Feature固有コンポーネントは各Featureに統合
3. 不要/未使用コンポーネントを特定
4. 空ディレクトリを削除

### 対応方針

#### 1. Shared UI Componentsへの移行
以下を`src/shared/ui/components/`に移行:
- `TypewriterText.tsx` → `@shared/ui`
- `VerticalActionButton.tsx` → `@shared/ui`
- `AnimatedStatistic.tsx` → `@shared/ui`
- `StatisticCard.tsx` → `@shared/ui`
- `TrendChart.tsx` → `@shared/ui`
- `DiffIndicator.tsx` → `@shared/ui`

#### 2. Feature固有コンポーネント
- `ReportStepIndicator.tsx` → `@features/report/ui/` または `@features/chat/ui/`
  - 2箇所で使用（ChatPage、Report系）
  - 汎用性があるため`@shared/ui`も検討

#### 3. 削除候補
- `DownloadButton_.tsx` - 名前に`_`、使用状況不明
- `components/Report/` - 既に移行済み
- `components/Utils/AnimatedStatistic.tsx` - ui/と重複
- `components/examples/` - サンプルコード
- `components/debug/` - デバッグ用、本番不要

#### 4. Dashboard Components
- `components/ManagementDashboard/` (6 files)
  - Phase 7で Dashboard Feature として統合

#### 5. 空ディレクトリ削除
- `components/analysis/`
- `components/common/`

## 📋 Phase 6実施計画

### Step 1: Shared UI Migration (汎用コンポーネント移行)
**所要時間**: 30分

#### 移行対象 (6 files)
1. `TypewriterText.tsx` → `shared/ui/components/TypewriterText.tsx`
2. `VerticalActionButton.tsx` → `shared/ui/components/VerticalActionButton.tsx`
3. `AnimatedStatistic.tsx` → `shared/ui/components/AnimatedStatistic.tsx`
4. `StatisticCard.tsx` → `shared/ui/components/StatisticCard.tsx`
5. `TrendChart.tsx` → `shared/ui/components/TrendChart.tsx`
6. `DiffIndicator.tsx` → `shared/ui/components/DiffIndicator.tsx`

#### 作業内容
1. ファイル移動
2. `shared/ui/index.ts`にエクスポート追加
3. 使用箇所のimport更新（3箇所）
4. ビルド検証

### Step 2: ReportStepIndicator の適切配置
**所要時間**: 15分

#### 選択肢
- **Option A**: `@shared/ui`へ移行（推奨）
  - 理由: ChatとReportの両方で使用、汎用性あり
- **Option B**: `@features/report`へ移行
  - 理由: 名前が`Report`だが、実際はステップ表示の汎用コンポーネント

**推奨**: Option A (`@shared/ui`)

### Step 3: 不要ファイル・ディレクトリ削除
**所要時間**: 10分

#### 削除対象
1. `components/Report/` - 既に移行済み
2. `components/Utils/AnimatedStatistic.tsx` - ui/と重複
3. `components/examples/` - サンプルコード
4. `components/debug/` - デバッグ用（オプション）
5. `components/analysis/` - 空ディレクトリ
6. `components/common/` - 空ディレクトリ
7. `components/DownloadButton_.tsx` - 未使用（要確認）

### Step 4: 残存コンポーネントの整理
**所要時間**: 10分

#### 保留（Phase 7以降で対応）
- `components/ManagementDashboard/` (6 files)
  - Dashboard Feature化で対応
- `components/TokenPreview/` (1 file)
  - Utils/Debug系として維持
- `components/rag/` (1 file)
  - RAG Feature化で対応

## 📊 実施スコープ

### Phase 6で実施
✅ Shared UI Componentsへの移行（6ファイル）  
✅ ReportStepIndicatorの配置（1ファイル）  
✅ 不要ファイル・ディレクトリ削除（7項目）  
✅ Import参照の更新（約10箇所）

### Phase 6で実施しない
❌ Dashboard Components（Phase 7へ）  
❌ TokenPreview（維持）  
❌ RAG Components（Phase 8へ）

## 🎯 成功基準

1. ✅ 汎用UIコンポーネントが`@shared/ui`に配置
2. ✅ すべてのimport参照が更新
3. ✅ ビルドエラーなし
4. ✅ 不要ファイルが削除
5. ✅ 空ディレクトリが削除

## 📝 次のアクション

### Phase 6開始準備
```bash
git checkout -b phase6/component-cleanup
```

### 実施順序
1. Step 1: Shared UI Migration
2. Step 2: ReportStepIndicator配置
3. Step 3: 不要ファイル削除
4. Step 4: ビルド検証
5. ドキュメント作成
6. コミット

---

**Phase 6 準備完了!**  
「次に進んで」でPhase 6を開始します。
