# Migration Status - Feature-Sliced Design

## 全体進捗

| Phase | ステータス | 完了日 | 概要 |
|-------|----------|--------|------|
| Phase 1 | ✅ 完了 | 2025-09-XX | ディレクトリ構造作成・Path Alias設定 |
| Phase 2 | ✅ 完了 | 2025-10-03 | Shared層インポートパス置換 (40ファイル) |
| Phase 3 | ✅ 完了 | 2025-10-03 | Features層ドキュメント整備 |
| Phase 4 | ⏳ 計画中 | TBD | Feature完全移行 (段階的) |
| Phase 5 | 📋 未着手 | TBD | Pages層整理 |
| Phase 6 | 📋 未着手 | TBD | 完全なFSD達成 |

---

## Phase 1: 基盤整備 ✅

### 実施内容
- [x] FSDディレクトリ構造作成
- [x] Path Alias設定 (tsconfig.json, vite.config.ts)
- [x] 各層のREADME.md作成

### ディレクトリ構造
```
src/
├── app/
├── pages/
├── widgets/
├── features/
│   ├── notification/      # Phase 1で作成
│   ├── report/            # Phase 3で作成
│   ├── database/          # Phase 3で作成
│   ├── manual/            # Phase 3で作成
│   └── chat/              # Phase 3で作成
├── entities/
└── shared/
    ├── infrastructure/    # Phase 1で作成
    ├── utils/             # Phase 1で作成
    ├── types/             # Phase 1で作成
    ├── hooks/ui/          # Phase 1で作成
    ├── ui/                # Phase 1で作成
    └── constants/         # Phase 1で作成
```

### Path Aliases (20+)
```typescript
@features/*, @shared/*, @app/*, @pages/*, @widgets/*,
@components/*, @hooks/*, @stores/*, @types/*, @utils/*,
@config/*, @constants/*, @layout/*, @theme/*, @services/*,
@entities/*, @domain/*, @infra/*, @controllers/*
```

---

## Phase 2: Shared層インポートパス置換 ✅

### 実施内容
横断的機能を `@shared` パスに統一

#### HTTPClient Migration (5ファイル)
- [x] `BlockUnitPriceInteractive.tsx`
- [x] `CustomerListAnalysis.tsx`
- [x] `SolvestNavi.tsx`
- [x] `chatService.ts`
- [x] `manualsApi.ts`

**パターン**: `@/services/httpClient` → `@shared/infrastructure/http`

#### Types Migration (2ファイル)
- [x] `shared/infrastructure/http/httpClient_impl.ts`
- [x] `services/httpClient_impl.ts`

**パターン**: `@/types/api` → `@shared/types`

#### Utils Migration (6ファイル)
- [x] `ManualPage.tsx` (anchors)
- [x] `ManualModal.tsx` (anchors)
- [x] `useCsvUploadArea.ts` (validators, csvPreview)
- [x] `PdfPreviewModal.tsx` (pdfWorkerLoader)
- [x] `PDFViewer.tsx` (pdfWorkerLoader)

**パターン**: `@/utils/*` → `@shared/utils/*`

#### UI Hooks Migration (27ファイル)
**Layout層** (5ファイル):
- [x] `MainLayout.tsx`
- [x] `Sidebar.tsx`
- [x] `ThemeProvider.tsx`

**Pages層** (4ファイル):
- [x] `PortalPage.tsx`
- [x] `ManualPage.tsx`
- [x] `ShogunManualList.tsx`
- [x] `SolvestNavi.tsx`

**Components層** (18ファイル):
- [x] shared/ui/* (2)
- [x] components/ui/* (2)
- [x] components/debug/* (1)
- [x] components/Report/common/* (9)
- [x] components/Report/viewer/* (1)
- [x] components/chat/* (2)
- [x] components/common/csv-upload/* (2)

**パターン**: `@/hooks/ui` or relative → `@shared/hooks/ui`

### 成果
- ✅ **40ファイル**のインポートパス置換完了
- ✅ ビルド成功 (8.09秒)
- ✅ 型エラーなし
- ✅ 実行エラーなし

---

## Phase 3: Features層ドキュメント整備 ✅

### 実施内容
各featureの責務・構造を文書化

#### ドキュメント作成
- [x] `features/notification/README.md` (既存)
- [x] `features/report/README.md`
- [x] `features/database/README.md`
- [x] `features/manual/README.md`
- [x] `features/chat/README.md`
- [x] `ARCHITECTURE.md` (全体アーキテクチャ)
- [x] `PHASE3_SIMPLIFIED.md` (簡略版計画)

### 文書化された機能

#### 1. Notification ✅ (完全移行済み)
- **配置**: `features/notification/`
- **構造**: model/controller/view分離
- **状態**: Phase 1-2で完全移行完了

#### 2. Report 📝 (文書化済み)
- **配置**: `components/Report/`, `hooks/report/`
- **主要機能**:
  - レポート生成 (PDF/Excel)
  - CSVアップロード
  - インタラクティブフロー
- **移行予定**: Phase 4

#### 3. Database 📝 (文書化済み)
- **配置**: `components/database/`, `hooks/database/`
- **主要機能**:
  - CSVアップロード
  - データ検証
  - プレビュー
- **移行予定**: Phase 4

#### 4. Manual 📝 (文書化済み)
- **配置**: `components/manual/`, `services/api/manualsApi.ts`
- **主要機能**:
  - マニュアル表示
  - 検索
  - 目次ナビゲーション
- **移行予定**: Phase 4

#### 5. Chat 📝 (文書化済み)
- **配置**: `components/chat/`, `services/chatService.ts`
- **主要機能**:
  - AI質問応答
  - PDFプレビュー
  - 質問テンプレート
- **移行予定**: Phase 4

### 成果
- ✅ 5つのfeatureがドキュメント化
- ✅ アーキテクチャ原則明確化
- ✅ 開発者オンボーディング資料完備

---

## Phase 4: Feature完全移行 (進行中) 🔄

### 方針
**段階的移行**: 新規開発・大規模修正時に該当featureを移行

### 優先順位

#### 高優先度 - Report機能 (進行中)

##### Step 3-1: Report設定の移行 ✅ (完了 - 2025/10/03)
- [x] `src/constants/reportConfig/` → `features/report/config/reportConfig/`
- [x] `src/constants/CsvDefinition.ts` → `features/report/config/CsvDefinition.ts`
- [x] `src/types/reportBase.ts` → `features/report/model/report.types.ts`
- [x] `src/types/report.ts` → `features/report/model/report-api.types.ts`
- [x] 公開API作成: `features/report/index.ts`
- [x] インポートパス更新 (affected files: 16)
- [x] ビルド成功確認

**成果**:
- Report設定が完全にFSD構造に移行
- 16ファイルのインポートパスを `@features/report` に更新
- ビルド時間: 8.47秒 (エラーなし)

---

##### Step 3-2: Report Hooks の移行 (次のステップ) ⏳
- [ ] `src/hooks/report/useReportManager.ts` → `features/report/hooks/useReportManager.ts`
- [ ] `src/hooks/report/useReportGeneration.ts` → `features/report/hooks/useReportGeneration.ts`
- [ ] `src/hooks/report/useReportPreview.ts` → `features/report/hooks/useReportPreview.ts`
- [ ] `src/hooks/report/useReportBaseBusiness.ts` → `features/report/hooks/useReportBaseBusiness.ts`
- [ ] インポートパス更新
- [ ] 公開API更新

**推定工数**: 3-4時間  
**リスク**: 中 (ビジネスロジック含む、テストが必要)

---

##### Step 3-3: Report共通UIの移行 📋 (未着手)
- [ ] `src/components/Report/common/` → `features/report/ui/common/`

##### Step 3-4: Report個別UIの移行 📋 (未着手)
- [ ] `src/components/Report/ReportBase.tsx` → `features/report/ui/ReportBase.tsx`

##### Step 3-5: Interactive Report の移行 📋 (未着手)
- [ ] `src/components/Report/interactive/` → `features/report/ui/interactive/`

---

#### 高優先度 - Database機能 (Step 3完了後)
2. **Database機能** (CSV処理改善時)
   - [ ] components/database/ → features/database/ui/
   - [ ] hooks/database/ → features/database/hooks/

#### 中優先度
3. **Manual機能** (マニュアル検索機能追加時)
   - [ ] components/manual/ → features/manual/ui/
   - [ ] services/api/manualsApi.ts → features/manual/api/
   - [ ] types/manuals.ts → features/manual/model/

4. **Chat機能** (AI応答改善時)
   - [ ] components/chat/ → features/chat/ui/
   - [ ] services/chatService.ts → features/chat/api/

#### 低優先度
5. **Analysis機能**
6. **Dashboard機能**

### 移行手順 (テンプレート)
```bash
# 1. ディレクトリ作成
mkdir -p src/features/[feature]/{model,controller,view,hooks,ui,api,config}

# 2. ファイルコピー
cp src/components/[Feature]/* src/features/[feature]/ui/
cp src/hooks/[feature]/* src/features/[feature]/hooks/

# 3. インポートパス更新
# (一括置換ツール使用)

# 4. 公開API作成
# features/[feature]/index.ts

# 5. ビルド確認
npm run build

# 6. コミット
git add src/features/[feature]
git commit -m "feat: migrate [feature] to FSD structure"
```

---

## Phase 5: Pages層整理 (未着手) 📋

### 計画
- [ ] ページコンポーネントをWidgets/Featuresに分解
- [ ] ルーティング定義の最適化
- [ ] Lazy Loading適用

### 対象
- `pages/report/` → widgets/report-page
- `pages/manual/` → widgets/manual-page
- `pages/database/` → widgets/database-page

---

## Phase 6: 完全なFSD達成 (未着手) 📋

### ゴール
- [ ] 全featureがFSD構造に準拠
- [ ] 循環依存の完全排除
- [ ] 完全なレイヤー分離
- [ ] E2Eテスト整備

---

## メトリクス

### コード品質
| 指標 | Phase 2完了時 | Phase 3完了時 | Phase 6目標 |
|------|--------------|--------------|-------------|
| ビルドエラー | 0 | 0 | 0 |
| 型エラー | 0 | 0 | 0 |
| ESLint警告 | ~10 | ~10 | 0 |
| Feature独立性 | 20% | 20% | 100% |
| ドキュメント化 | 40% | 80% | 100% |

### パフォーマンス
| 指標 | 現状 | Phase 6目標 |
|------|-----|-------------|
| ビルド時間 | 8.09s | < 10s |
| Main Bundle | 649KB | < 500KB |
| FCP | ~2s | < 1.5s |
| LCP | ~3s | < 2.5s |

---

## リスクと課題

### 高リスク
1. **循環依存**: Report ↔ Database ↔ Manual
   - **対策**: 依存グラフ分析ツール導入
   
2. **大規模変更**: 100+ファイルに影響
   - **対策**: 段階的移行 (Phase 4)

### 中リスク
3. **型定義の分離**: 共有型の取り扱い
   - **対策**: shared/types/ に集約維持

4. **テストカバレッジ**: 移行後のテスト
   - **対策**: Phase 6でテスト整備

### 低リスク
5. **ドキュメントの陳腐化**
   - **対策**: PR時にREADME更新チェック

---

## 今後のロードマップ

### Q4 2025
- [x] Phase 1-3完了
- [ ] Phase 4開始 (Report機能)

### Q1 2026
- [ ] Phase 4継続 (Database, Manual機能)
- [ ] テスト整備開始

### Q2 2026
- [ ] Phase 4完了 (全Feature移行)
- [ ] Phase 5開始 (Pages層整理)

### Q3 2026
- [ ] Phase 6 (完全FSD達成)
- [ ] E2Eテスト整備

---

## 参照ドキュメント

- `ARCHITECTURE.md` - アーキテクチャ全体像
- `PHASE2_COMPLETION_REPORT.md` - Phase 2詳細レポート
- `PHASE3_SIMPLIFIED.md` - Phase 3簡略版計画
- `features/*/README.md` - 各Feature詳細
- `shared/README.md` - Shared層詳細

---

**最終更新**: 2025年10月3日  
**現在のPhase**: Phase 3完了  
**次のマイルストーン**: Phase 4 (Feature完全移行)
