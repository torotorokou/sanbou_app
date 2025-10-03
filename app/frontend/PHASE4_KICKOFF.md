# Phase 4 キックオフ - Feature完全移行

## 実施開始日
2025年10月3日

---

## 🎯 Phase 4の目標

### 最終ゴール
全ての機能をFeature-Sliced Design (FSD) 構造に完全移行し、以下を達成する:

1. **Feature独立性**: 各Featureが独立して開発・テスト可能
2. **明確な責務**: 各Featureの役割と境界が明確
3. **循環依存の排除**: Feature間の依存が一方向
4. **テスタビリティ**: ユニットテスト・統合テストの実装が容易

---

## 📋 Phase 4の戦略

### アプローチ: 段階的移行 (Incremental Migration)

**大規模一括移行を避ける理由**:
1. プロダクションリスクが高い
2. コードレビューが困難
3. バグの特定が難しい
4. ロールバックが困難

**段階的移行のメリット**:
1. 各ステップで動作確認
2. 小さな単位でコードレビュー
3. 問題の早期発見
4. 並行開発が可能

---

## 🗺️ Phase 4 ロードマップ

### Step 1: 共通UIコンポーネントの移行 ✅ (完了)
**対象**: `src/shared/ui/` (既にPhase 2で完了)

**内容**:
- AnimatedStatistic
- DiffIndicator
- ReportStepIndicator
- StatisticCard
- TrendChart
- TypewriterText
- VerticalActionButton
- DownloadButton

**ステータス**: ✅ 完了 (Phase 2で実施済み)

---

### Step 2: Notification機能の完全移行 ✅ (完了)
**対象**: `features/notification/` (既にPhase 1-2で完了)

**構造**:
```
features/notification/
├── model/                 # 型定義・Zustandストア
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

**ステータス**: ✅ 完了

---

### Step 3: Report機能の段階的移行 (現在のフォーカス) 🎯

#### Step 3-1: Report設定の移行
**対象**: Report機能の設定ファイル

**移行内容**:
- [ ] `src/constants/reportConfig.ts` → `features/report/config/reportConfig.ts`
- [ ] `src/types/reportBase.ts` → `features/report/model/report.types.ts`
- [ ] 公開API作成: `features/report/index.ts`
- [ ] インポートパス更新 (affected files: ~15)

**推定工数**: 2-3時間  
**リスク**: 低 (設定ファイルのみ、ロジック変更なし)

---

#### Step 3-2: Report Hooks の移行
**対象**: Reportビジネスロジック

**移行内容**:
- [ ] `src/hooks/report/useReportManager.ts` → `features/report/hooks/useReportManager.ts`
- [ ] `src/hooks/report/useReportGeneration.ts` → `features/report/hooks/useReportGeneration.ts`
- [ ] `src/hooks/report/useReportPreview.ts` → `features/report/hooks/useReportPreview.ts`
- [ ] インポートパス更新 (affected files: ~20)

**推定工数**: 3-4時間  
**リスク**: 中 (ビジネスロジック含む、テストが必要)

---

#### Step 3-3: Report共通UIの移行
**対象**: Report機能で共有されるUIコンポーネント

**移行内容**:
- [ ] `src/components/Report/common/` → `features/report/ui/common/`
  - ReportHeader.tsx
  - ReportSelector.tsx
  - CsvUploadSection.tsx
  - PreviewSection.tsx
  - ActionsSection.tsx
  - SampleSection.tsx
- [ ] インポートパス更新 (affected files: ~10)

**推定工数**: 3-4時間  
**リスク**: 中 (コンポーネント間の依存関係)

---

#### Step 3-4: Report個別UIの移行
**対象**: ReportBaseとページコンポーネント

**移行内容**:
- [ ] `src/components/Report/ReportBase.tsx` → `features/report/ui/ReportBase.tsx`
- [ ] `src/pages/report/ReportFactory.tsx` 更新 (import変更のみ)
- [ ] `src/pages/report/ReportManagePage.tsx` 更新 (import変更のみ)
- [ ] インポートパス更新 (affected files: ~5)

**推定工数**: 2-3時間  
**リスク**: 中

---

#### Step 3-5: Interactive Report の移行
**対象**: インタラクティブレポート (ブロック単価等)

**移行内容**:
- [ ] `src/components/Report/interactive/` → `features/report/ui/interactive/`
  - BlockUnitPriceInteractive.tsx
  - BlockUnitPriceInteractiveModal.tsx
- [ ] インポートパス更新 (affected files: ~3)

**推定工数**: 2時間  
**リスク**: 低

---

### Step 4: Database機能の移行 (Step 3完了後)

#### Step 4-1: Database設定・型の移行
- [ ] CSV関連の型定義移行
- [ ] バリデーションルール移行

#### Step 4-2: Database Hooks の移行
- [ ] `useCsvUploadHandler.ts` → `features/database/hooks/`
- [ ] `useCsvValidation.ts` → `features/database/hooks/`

#### Step 4-3: Database UI の移行
- [ ] `components/database/` → `features/database/ui/`
- [ ] `components/common/csv-upload/` → `features/database/ui/csv-upload/`

**推定工数**: 4-5時間  
**リスク**: 中 (Report機能と依存関係あり)

---

### Step 5: Manual機能の移行 (Step 4完了後)

#### Step 5-1: Manual API の移行
- [ ] `services/api/manualsApi.ts` → `features/manual/api/manualsApi.ts`

#### Step 5-2: Manual型の移行
- [ ] `types/manuals.ts` → `features/manual/model/manual.types.ts`

#### Step 5-3: Manual UI の移行
- [ ] `components/manual/` → `features/manual/ui/`

**推定工数**: 3-4時間  
**リスク**: 低 (比較的独立している)

---

### Step 6: Chat機能の移行 (Step 5完了後)

#### Step 6-1: Chat API の移行
- [ ] `services/chatService.ts` → `features/chat/api/chatService.ts`

#### Step 6-2: Chat UI の移行
- [ ] `components/chat/` → `features/chat/ui/`

**推定工数**: 3-4時間  
**リスク**: 低

---

## 📊 Phase 4 全体スケジュール

| Step | 機能 | 推定工数 | 優先度 | ステータス |
|------|------|---------|--------|----------|
| 1 | 共通UI | - | - | ✅ 完了 |
| 2 | Notification | - | - | ✅ 完了 |
| 3-1 | Report設定 | 2-3h | 高 | ⏳ 準備中 |
| 3-2 | Report Hooks | 3-4h | 高 | 📋 未着手 |
| 3-3 | Report共通UI | 3-4h | 高 | 📋 未着手 |
| 3-4 | Report個別UI | 2-3h | 高 | 📋 未着手 |
| 3-5 | Interactive Report | 2h | 高 | 📋 未着手 |
| 4 | Database | 4-5h | 高 | 📋 未着手 |
| 5 | Manual | 3-4h | 中 | 📋 未着手 |
| 6 | Chat | 3-4h | 中 | 📋 未着手 |
| **合計** | - | **22-31h** | - | **Step 3-1開始** |

---

## ✅ 各Stepの完了基準

### 必須チェック項目
1. **ファイル移行**: すべてのファイルが正しい場所に配置
2. **インポートパス更新**: すべての依存ファイルのimportを更新
3. **公開API作成**: `index.ts` で公開APIを定義
4. **ビルド成功**: `npm run build` がエラーなく完了
5. **ESLint成功**: `npm run lint` がエラーなく完了
6. **動作確認**: 該当機能が正常に動作
7. **ドキュメント更新**: README.md, MIGRATION_STATUS.md更新

### 推奨チェック項目
8. **テスト実装**: ユニットテスト作成 (Phase 6で本格実施)
9. **コードレビュー**: チームメンバーによるレビュー
10. **パフォーマンス確認**: ビルドサイズ、実行速度確認

---

## 🚧 リスク管理

### 高リスク項目
1. **循環依存**: Report ↔ Database の相互依存
   - **対策**: 依存方向を明確化 (Report → Database のみ許可)
   - **検証**: `madge` 等の循環依存チェックツール導入

2. **大規模変更**: Report機能は50+ファイル
   - **対策**: Step 3を5つのサブステップに分割
   - **検証**: 各Stepで動作確認

### 中リスク項目
3. **型定義の分離**: 共有型 vs Feature固有型
   - **対策**: 共有型は `shared/types/` に維持
   - **検証**: TypeScript コンパイラでチェック

4. **既存ページへの影響**: import変更による破壊的変更
   - **対策**: 段階的移行、徹底的なテスト
   - **検証**: 全ページの動作確認

---

## 📝 移行チェックリスト (テンプレート)

### Step 3-1: Report設定の移行 (例)

#### 準備
- [ ] ブランチ作成: `git checkout -b phase4/step3-1-report-config`
- [ ] ディレクトリ確認: `features/report/config/`, `features/report/model/` 存在確認

#### ファイル移行
- [ ] `cp src/constants/reportConfig.ts features/report/config/reportConfig.ts`
- [ ] `cp src/types/reportBase.ts features/report/model/report.types.ts`

#### インポートパス更新
- [ ] `grep_search` で `reportConfig` の使用箇所特定
- [ ] 各ファイルの import を `@features/report` に更新
- [ ] `grep_search` で `reportBase` の使用箇所特定
- [ ] 各ファイルの import を `@features/report` に更新

#### 公開API作成
- [ ] `features/report/index.ts` 作成
- [ ] 必要なexportを定義

#### 検証
- [ ] `npm run build` 成功確認
- [ ] `npm run lint` 成功確認
- [ ] ブラウザで動作確認 (Report生成)

#### ドキュメント更新
- [ ] `MIGRATION_STATUS.md` 更新
- [ ] `features/report/README.md` 更新

#### コミット
- [ ] `git add .`
- [ ] `git commit -m "feat(phase4): migrate report config and types (Step 3-1)"`

---

## 🎯 今日の目標: Step 3-1 完了

### 実施内容
1. Report設定ファイルの移行
2. Report型定義の移行
3. 公開API作成
4. インポートパス更新
5. 動作確認

### 期待される成果
- ✅ `features/report/config/reportConfig.ts` 作成
- ✅ `features/report/model/report.types.ts` 作成
- ✅ `features/report/index.ts` 作成
- ✅ 15ファイルのインポートパス更新
- ✅ ビルド成功
- ✅ Report機能の動作確認

---

## 📚 参考ドキュメント
- `ARCHITECTURE.md` - FSDアーキテクチャ詳細
- `MIGRATION_STATUS.md` - 移行進捗トラッキング
- `features/notification/README.md` - 完了したFeatureの例
- `features/report/README.md` - Report機能の現状

---

**Phase 4開始**: 2025年10月3日  
**現在のStep**: Step 3-1 (Report設定の移行)  
**次のマイルストーン**: Step 3完了 (Report機能完全移行)
