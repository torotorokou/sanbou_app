# Migration Status - Feature-Sliced Design

## 全体進捗

| Phase | ステータス | 完了日 | 概要 |
|-------|----------|--------|------|
| Phase 1 | ✅ 完了 | 2025-09-XX | ディレクトリ構造作成・Path Alias設定 |
| Phase 2 | ✅ 完了 | 2025-10-03 | Shared層インポートパス置換 (40ファイル) |
| Phase 3 | ✅ 完了 | 2025-10-03 | Features層ドキュメント整備 |
| Phase 4 | 🔄 進行中 | TBD | Feature完全移行 (Report✅ Database✅ Manual✅ Chat未着手) |
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

#### 高優先度 - Report機能 ✅ (完了 - 2025/01/05)

**全体統計**:
- ✅ 34ファイル移行完了
- ✅ ~3,464行のコード
- ✅ 48の公開API
- ✅ 全ビルド成功
- ✅ 機能検証完了

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

**詳細レポート**: [PHASE4_STEP3-1_COMPLETION.md](../../docs/phase4/PHASE4_STEP3-1_COMPLETION.md)

---

##### Step 3-2: Report Hooks の移行 ✅ (完了 - 2025/01/05)
- [x] `src/hooks/report/useReportManager.ts` → `features/report/hooks/useReportManager.ts`
- [x] `src/hooks/report/useReportBaseBusiness.ts` → `features/report/hooks/useReportBaseBusiness.ts`
- [x] `src/hooks/report/useReportActions.ts` → `features/report/hooks/useReportActions.ts`
- [x] `src/hooks/report/useReportLayoutStyles.ts` → `features/report/hooks/useReportLayoutStyles.ts`
- [x] インポートパス修正 (2ファイル)
- [x] 公開API更新 (4つのhookをエクスポート)
- [x] コンシューマー更新 (3ファイル)
- [x] ビルド成功確認

**成果**:
- Reportビジネスロジックフックが完全にFSD構造に移行
- 3つのページコンポーネントのインポートパスを `@features/report` に更新
- クロスフィーチャー依存を絶対パスで管理 (`@/hooks/data/`)
- ビルド時間: 10.43秒 (エラーなし、Rollup警告は予想通り)

**詳細レポート**: [PHASE4_STEP3-2_COMPLETION.md](../../docs/phase4/PHASE4_STEP3-2_COMPLETION.md)

---

##### Step 3-3: Report共通UIの移行 ✅ (完了 - 2025/01/05)
- [x] `src/components/Report/common/` → `features/report/ui/common/` (13ファイル)
- [x] インポートパス修正 (8ファイル内部、4コンシューマー)
- [x] 公開API更新 (10コンポーネント + 4型 + 1ユーティリティ)
- [x] ビルド成功確認

**成果**:
- 共通UIコンポーネントが完全にFSD構造に移行
- ビルド時間: 8.26秒 (エラーなし)

---

##### Step 3-4: ReportBase の移行 ✅ (完了 - 2025/01/05)
- [x] `src/components/Report/ReportBase.tsx` → `features/report/ui/ReportBase.tsx`
- [x] インポートパス修正 (11箇所)
- [x] 公開API更新
- [x] コンシューマー更新 (3ページ)
- [x] ビルド成功確認

**成果**:
- メインコンテナコンポーネントが完全にFSD構造に移行
- ビルド時間: 8.47秒 (エラーなし)

---

##### Step 3-5: Interactive Components の移行 ✅ (完了 - 2025/01/05)
- [x] `src/components/Report/interactive/` → `features/report/ui/interactive/` (5ファイル)
- [x] インポートパス修正 (2ファイル)
- [x] 公開API更新 (2コンポーネント + 2型 + 1ユーティリティ)
- [x] ビルド成功確認

**成果**:
- インタラクティブコンポーネントが完全にFSD構造に移行

---

##### Step 3-6: Viewer Components の移行 ✅ (完了 - 2025/01/05)
- [x] `src/components/Report/viewer/` → `features/report/ui/viewer/` (2ファイル)
- [x] インポートパス修正 (2ファイル)
- [x] 公開API更新 (2コンポーネント)
- [x] ビルド成功確認

**成果**:
- Viewerコンポーネントが完全にFSD構造に移行
- ビルド時間: 8.11秒 (エラーなし)

---

**Report機能移行完了レポート**: [PHASE4_STEP3_COMPLETION.md](../../docs/phase4/PHASE4_STEP3_COMPLETION.md)

**最終的な構造**:
```
src/features/report/
├── config/          # 設定 (Step 3-1)
├── model/           # 型定義 (Step 3-1)
├── hooks/           # ビジネスロジック (Step 3-2)
├── ui/
│   ├── common/      # 共通UI (Step 3-3)
│   ├── interactive/ # インタラクティブ (Step 3-5)
│   ├── viewer/      # ビューアー (Step 3-6)
│   └── ReportBase.tsx # メイン (Step 3-4)
└── index.ts         # 公開API (48エクスポート)
```

---

#### 高優先度 - Database機能 ✅ (完了 - 2025/01/05)

**全体統計**:
- ✅ 7ファイル移行完了
- ✅ ~600行のコード
- ✅ 7の公開API
- ✅ 全ビルド成功
- ✅ 所要時間: 約30分

##### Step 4-1: 型定義の移行 ✅
- [x] `components/database/types.ts` → `features/database/model/database.types.ts`
- [x] 公開API作成

##### Step 4-2: Hooksの移行 ✅
- [x] `hooks/database/` → `features/database/hooks/` (3ファイル)
- [x] 公開API更新 (2フック)
- [x] ビルド時間: 7.76秒

##### Step 4-3: UIコンポーネントの移行 ✅
- [x] `components/database/` → `features/database/ui/` (3ファイル)
- [x] インポートパス修正 (1ファイル)
- [x] 公開API更新 (3コンポーネント)
- [x] ビルド時間: 7.98秒

##### Step 4-4: Consumer更新 ✅
- [x] `pages/database/UploadDatabasePage.tsx` インポート統合
- [x] ビルド時間: 8.42秒

**最終的な構造**:
```
src/features/database/
├── model/           # 型定義 (Step 4-1)
├── hooks/           # ビジネスロジック (Step 4-2)
├── ui/              # UIコンポーネント (Step 4-3)
└── index.ts         # 公開API (7エクスポート)
```

**詳細レポート**: 
- [PHASE4_STEP4_KICKOFF.md](../../docs/phase4/PHASE4_STEP4_KICKOFF.md) - 計画書
- [PHASE4_STEP4_COMPLETION.md](../../docs/phase4/PHASE4_STEP4_COMPLETION.md) - 完了レポート

---

#### 中優先度 - Manual機能 ✅ (完了 - 2025/01/05)

**全体統計**:
- ✅ 2ファイル移行完了
- ✅ ~100行のコード
- ✅ 8の公開API
- ✅ 所要時間: 約20分

##### Step 5-1: 型定義の移行 ✅
- [x] `types/manuals.ts` → `features/manual/model/manual.types.ts`
- [x] ManualCatalogResponse型を追加
- [x] 公開API作成 (6型)

##### Step 5-2: APIサービスの移行 ✅
- [x] `services/api/manualsApi.ts` → `features/manual/api/manualsApi.ts`
- [x] インポートパス修正
- [x] 型定義の再配置
- [x] 公開API更新 (named + default exports)

##### Step 5-3: Consumer更新 ✅
- [x] 4つのページコンポーネント更新
  - `pages/manual/ShogunManualList.tsx`
  - `pages/manual/ManualPage.tsx`
  - `pages/manual/GlobalManualSearch.tsx`
  - `pages/manual/ManualModal.tsx`

**最終的な構造**:
```
src/features/manual/
├── model/           # 型定義 (Step 5-1)
├── api/             # APIサービス (Step 5-2)
└── index.ts         # 公開API (8エクスポート)
```

**詳細レポート**: 
- [PHASE4_STEP5_KICKOFF.md](../../docs/phase4/PHASE4_STEP5_KICKOFF.md) - 計画書
- [PHASE4_STEP5_COMPLETION.md](../../docs/phase4/PHASE4_STEP5_COMPLETION.md) - 完了レポート

---

#### 中優先度 - Chat機能 (次回実施予定)
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
| 指標 | Phase 2完了時 | Phase 3完了時 | Phase 4 (Report完了) | Phase 6目標 |
|------|--------------|--------------|---------------------|-------------|
| ビルドエラー | 0 | 0 | 0 | 0 |
| 型エラー | 0 | 0 | 0 | 0 |
| ESLint警告 | ~10 | ~10 | ~10 | 0 |
| Feature独立性 | 20% | 20% | 40% | 100% |
| ドキュメント化 | 40% | 80% | 85% | 100% |
| 移行済みFeature | 1/5 | 1/5 | 2/5 | 5/5 |

### パフォーマンス
| 指標 | 現状 | Phase 6目標 |
|------|-----|-------------|
| ビルド時間 | ~8.5s | < 10s |
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
- [x] Phase 4開始 (Report機能) ✅

### Q1 2026
- [ ] Phase 4継続 (Database, Manual, Chat機能)
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
- `docs/phase4/PHASE4_STEP3_COMPLETION.md` - Report機能完全移行レポート ✅
- `docs/phase4/PHASE4_STEP3-1_COMPLETION.md` - Report設定・型定義移行
- `docs/phase4/PHASE4_STEP3-2_COMPLETION.md` - Reportフック移行
- `features/*/README.md` - 各Feature詳細
- `shared/README.md` - Shared層詳細

---

**最終更新**: 2025年1月5日  
**現在のPhase**: Phase 4進行中 (Report機能✅完了)  
**次のマイルストーン**: Phase 4継続 (Database機能移行)
