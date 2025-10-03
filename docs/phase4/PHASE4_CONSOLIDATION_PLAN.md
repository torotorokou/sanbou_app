# Phase 4: Feature Migration Consolidation Plan

**作成日**: 2025-10-03  
**目的**: Phase 4で完了した4つのフィーチャー移行を統合し、古いコードをクリーンアップ

## 📊 Phase 4 完了状況

| Step | Feature | Status | Branch | Files | Time | Commit |
|------|---------|--------|--------|-------|------|--------|
| 3 | Report | ✅ Complete | phase4/step3-5-interactive | 34 | 6h | a04cbd0 |
| 4 | Database | ✅ Complete | phase4/step4-database | 7 | 30min | 0696ec8 |
| 5 | Manual | ✅ Complete | phase4/step5-manual | 2 | 20min | 519b984 |
| 6 | Chat | ✅ Complete | phase4/step6-chat | 10 | 25min | f8db589 |

**合計**: 53ファイル、約7時間15分

## 🎯 Phase 4統合の目標

### 1. ブランチ統合
すべてのPhase 4ブランチを`develop`または`main`にマージ

### 2. 古いディレクトリのクリーンアップ
以下のディレクトリから移行済みファイルを削除:
- `src/components/Report/` → `src/features/report/`
- `src/components/database/` → `src/features/database/`
- `src/components/chat/` → `src/features/chat/`
- `src/types/` → 各feature/model/

### 3. インポートパスの最終確認
すべてのconsumerが`@features/*`を使用していることを確認

## 📋 実施手順

### Step 1: ブランチマージ準備

```bash
# 現在のブランチ確認
git branch --list "phase4/*"

# 各ブランチの状態確認
git log --oneline phase4/step3-5-interactive -5
git log --oneline phase4/step4-database -5
git log --oneline phase4/step5-manual -5
git log --oneline phase4/step6-chat -5
```

### Step 2: 統合ブランチ作成

```bash
# developブランチに切り替え（またはmainブランチ）
git checkout develop

# Phase 4統合ブランチ作成
git checkout -b phase4/consolidation

# 各フィーチャーブランチを順番にマージ
git merge phase4/step3-5-interactive --no-ff -m "Merge report feature migration"
git merge phase4/step4-database --no-ff -m "Merge database feature migration"
git merge phase4/step5-manual --no-ff -m "Merge manual feature migration"
git merge phase4/step6-chat --no-ff -m "Merge chat feature migration"
```

### Step 3: 古いファイルの削除

移行が完了し、すべてのconsumerが更新されたファイルを削除:

#### Report関連
- `src/components/Report/` (ReportBase.tsx以外)
- `src/types/report.ts` → features/report/model/に移行済み
- `src/hooks/report/` → features/report/hooks/に移行済み

#### Database関連
- `src/components/database/`全体
- `src/types/database.ts` → features/database/model/に移行済み
- `src/hooks/database/` → features/database/hooks/に移行済み

#### Manual関連
- `src/types/manual.ts` → features/manual/model/に移行済み
- `src/api/manuals.ts` → features/manual/api/に移行済み

#### Chat関連
- `src/components/chat/`全体
- `src/types/chat.ts` → features/chat/model/に移行済み
- `src/api/chatService.ts` → features/chat/api/に移行済み

### Step 4: ビルド検証

```bash
cd app/frontend
npm run build
npm run lint
```

### Step 5: テスト実行

```bash
# ユニットテスト（存在する場合）
npm test

# E2Eテスト（存在する場合）
npm run test:e2e
```

### Step 6: 最終コミット

```bash
git add -A
git commit -m "chore(phase4): Consolidate feature migrations and cleanup old directories

- Merged 4 feature branches (Report, Database, Manual, Chat)
- Removed old component directories after migration
- All imports updated to @features/* paths
- Total migration: 53 files, ~7.25 hours

Phase 4 Complete:
- features/report/: 34 files (config, model, hooks, ui)
- features/database/: 7 files (model, hooks, ui)
- features/manual/: 2 files (model, api)
- features/chat/: 10 files (model, api, ui)
"
```

## 🚦 次のフェーズ検討

### Phase 4で対応していない残存コンポーネント

#### 1. Analysis Feature (3 files)
- `components/analysis/customer-list-analysis/`
  - AnalysisProcessingModal.tsx
  - ComparisonConditionForm.tsx
  - CustomerComparisonResultCard.tsx

#### 2. Dashboard Feature (5 files)
- `components/ManagementDashboard/`
  - CustomerAnalysis.tsx
  - RevenuePanel.tsx
  - SummaryPanel.tsx
  - ProcessVolumePanel.tsx
  - BlockCountPanel.tsx

#### 3. UI Components (10 files)
- `components/ui/`
  - TypewriterText.tsx
  - DiffIndicator.tsx
  - StatisticCard.tsx
  - TrendChart.tsx
  - VerticalActionButton.tsx
  - ReportStepIndicator.tsx
  - AnimatedStatistic.tsx
  - など

#### 4. その他
- `components/TokenPreview/`
- `components/rag/`
- `components/examples/`
- `components/debug/`

### 推奨される次のステップ

#### Option A: Phase 4拡張 - 残りのFeature移行
Analysis、Dashboardフィーチャーを同様のパターンで移行

#### Option B: Phase 5 - Pages層のリファクタリング
`src/pages/`配下のページコンポーネントをFSDに適合させる

#### Option C: Phase 5 - Shared層の整理
`@shared/`の構造を見直し、UI Components層を整理

## 📝 判断基準

### Phase 4拡張を選択する場合:
- 残存フィーチャー（Analysis, Dashboard）が独立した機能単位である
- 早急に機能ごとの境界を明確にしたい
- チーム内でフィーチャーベースの開発体制を構築したい

### Phase 5に進む場合:
- 主要4フィーチャー（Report, Database, Manual, Chat）で十分な成果
- Pages層のリファクタリングが優先度高い
- UI Components層の整理が必要

## 🎯 推奨アクション

**現時点の推奨**: Phase 4統合 → Phase 5（Pages層リファクタリング）

理由:
1. 主要4フィーチャーで大部分のビジネスロジックをカバー
2. Analysis/DashboardはUI中心で、Pages層整理後の方が効率的
3. Phase 5でPages構造を整理すれば、残存機能の配置先も明確化

---

**次のアクション**: Phase 4統合作業の開始
