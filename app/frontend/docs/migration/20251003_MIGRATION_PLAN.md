# ファイル分類と移動計画

## 📋 分類基準

### ✅ shared へ移動（横断的・汎用的）

- どの機能にも依存しない汎用ユーティリティ
- 共通UI コンポーネント
- 共通型定義
- HTTPクライアントなどのインフラ層
- 汎用カスタムフック

### ✅ features へ移動（機能固有）

- 特定のビジネス機能に紐づくロジック
- 機能固有のAPI呼び出し
- 機能固有の型定義
- 機能固有のフック

---

## 📁 移動計画

### 1. src/utils → shared/utils + features

#### → src/shared/utils/

- ✅ `anchors.ts` - アンカー処理（マニュアル等で使用、汎用）
- ✅ `pdfWorkerLoader.ts` - PDF.jsワーカー読み込み（汎用）
- ✅ `responsiveTest.ts` - レスポンシブテスト（汎用）
- ⚠️ `notify.ts` - **互換性レイヤー、削除候補**（既に @features/notification に移行済み）
- ⚠️ `notify.test.ts` - **削除候補**（既に features/notification に移行済み）

#### → src/shared/utils/csv/

- ✅ `csvPreview.ts` - CSV プレビュー（汎用）

#### → src/shared/utils/validators/

- ✅ `validators/csvValidator.ts` - CSV バリデーション（汎用だが database 機能で使用）

### 2. src/types → shared/types + features

#### → src/shared/types/

- ✅ `api.ts` - 共通API型定義
- ✅ `yaml.d.ts` - YAML型定義（汎用）

#### → src/features/chat/model/

- ✅ `chat.ts` - チャット機能の型

#### → src/features/manual/model/

- ✅ `manuals.ts` - マニュアル機能の型

#### → src/features/navi/model/

- ✅ `navi.ts` - ナビゲーション機能の型

#### → src/features/report/model/

- ✅ `report.ts` - レポート機能の型
- ✅ `reportBase.ts` - レポート基本型

### 3. src/services → shared/infrastructure + features

#### → src/shared/infrastructure/http/

- ✅ `httpClient.ts` - HTTPクライアント公開API
- ✅ `httpClient_impl.ts` - HTTPクライアント実装

#### → src/services/api/ の各APIサービス

これらは機能固有のAPIクライアントなので features へ：

#### → src/features/chat/api/

- ✅ `chatService.ts` → `chatApi.ts`

#### → src/features/ai/api/

- ✅ `services/api/aiApiService.ts` → `aiApi.ts`

#### → src/features/database/api/

- ✅ `services/api/databaseApiService.ts` → `databaseApi.ts`

#### → src/features/ledger/api/

- ✅ `services/api/ledgerApiService.ts` → `ledgerApi.ts`

#### → src/features/manual/api/

- ✅ `services/api/manualsApi.ts` (既に存在)

### 4. src/hooks → shared/hooks + features

#### → src/shared/hooks/ui/

- ✅ `hooks/ui/useContainerSize.ts`
- ✅ `hooks/ui/useResponsive.ts`
- ✅ `hooks/ui/useScrollTracker.ts`
- ✅ `hooks/ui/useSidebarDefault.ts`
- ✅ `hooks/ui/useSidebarResponsive.ts`
- ✅ `hooks/ui/useWindowSize.ts`
- ✅ `useResponsive.ts` (ルートにある重複？)

#### → src/features/report/hooks/

- ✅ `useExcelGeneration.ts`
- ✅ `useReportActions.ts`
- ✅ `useReportBaseBusiness.ts`
- ✅ `useReportLayoutStyles.ts`
- ✅ `useReportManager.ts`
- ✅ `hooks/report/*`
- ✅ `hooks/data/*` (レポート関連のデータフック)

#### → src/features/database/hooks/

- ✅ `useCsvValidation.ts`
- ✅ `hooks/database/*`

#### → src/features/analysis/hooks/

- ✅ `hooks/analysis/*`

#### → src/features/factory/api/ (新規)

- ✅ `hooks/api/useFactoryReport.ts` → API層として整理

### 5. src/components → shared/ui + widgets + features

#### → src/shared/ui/

汎用的なUIコンポーネント：

- ✅ `components/ui/*` - 汎用UIコンポーネント
- ✅ `components/common/*` - 共通コンポーネント

#### → src/widgets/

ページ横断の大きめUI：

- ✅ `components/ManagementDashboard/` → `widgets/management-dashboard/`
- ✅ `components/TokenPreview/` → `widgets/token-preview/`
- ✅ `components/Utils/` → `widgets/utils/`

#### → src/features/{feature}/ui/

機能固有のUIコンポーネント：

- ✅ `components/chat/*` → `features/chat/ui/`
- ✅ `components/rag/*` → `features/rag/ui/`
- ✅ `components/Report/*` → `features/report/ui/`
- ✅ `components/database/*` → `features/database/ui/`
- ✅ `components/analysis/*` → `features/analysis/ui/`

#### → 保留

- ⚠️ `components/debug/` - デバッグ用、そのまま
- ⚠️ `components/examples/` - 例、そのまま

### 6. 新規 features の作成提案

#### src/features/chat/

```
chat/
├── model/
│   ├── chat.types.ts (from types/chat.ts)
│   └── chatStore.ts (将来)
├── api/
│   └── chatApi.ts (from services/chatService.ts)
├── ui/
│   ├── AnswerViewer.tsx
│   ├── ChatAnswerSection.tsx
│   └── ...
└── index.ts
```

#### src/features/manual/

```
manual/
├── model/
│   ├── manual.types.ts (from types/manuals.ts)
│   └── manualStore.ts (from stores/manualsStore.ts)
├── api/
│   └── manualApi.ts (from services/api/manualsApi.ts)
├── ui/
│   └── ... (将来、pages/manual から移動)
└── index.ts
```

#### src/features/report/

```
report/
├── model/
│   ├── report.types.ts (from types/report.ts)
│   └── reportBase.types.ts (from types/reportBase.ts)
├── hooks/
│   ├── useExcelGeneration.ts
│   ├── useReportActions.ts
│   └── ...
├── ui/
│   └── ... (from components/Report/)
└── index.ts
```

#### src/features/database/

```
database/
├── model/
│   └── database.types.ts
├── api/
│   └── databaseApi.ts (from services/api/databaseApiService.ts)
├── hooks/
│   └── useCsvValidation.ts
├── ui/
│   └── ... (from components/database/)
└── index.ts
```

#### src/features/ledger/

```
ledger/
├── api/
│   └── ledgerApi.ts (from services/api/ledgerApiService.ts)
└── index.ts
```

#### src/features/ai/

```
ai/
├── api/
│   └── aiApi.ts (from services/api/aiApiService.ts)
└── index.ts
```

#### src/features/navi/

```
navi/
├── model/
│   └── navi.types.ts (from types/navi.ts)
└── index.ts
```

---

## 🎯 優先順位

### Phase 1: インフラ層（高優先度）

1. ✅ services/httpClient → shared/infrastructure/http/
2. ✅ utils/anchors, pdfWorkerLoader, csvPreview → shared/utils/
3. ✅ utils/validators → shared/utils/validators/
4. ✅ types/api.ts, yaml.d.ts → shared/types/
5. ✅ hooks/ui/\* → shared/hooks/ui/
6. ✅ components/ui/\* → shared/ui/
7. ✅ components/common/\* → shared/ui/

### Phase 2: 機能レイヤー（中優先度）

1. ✅ chat 機能の整理
2. ✅ manual 機能の整理
3. ✅ report 機能の整理
4. ✅ database 機能の整理

### Phase 3: その他（低優先度）

1. ✅ ledger, ai, navi 機能の整理
2. ✅ widgets の整理
3. ✅ 互換性レイヤーの削除検討

---

## 📝 注意事項

1. **段階的な移行**: 一度にすべて移動せず、Phase 1 → Phase 2 → Phase 3 の順に実施
2. **import パスの更新**: 各 Phase 完了後に import パスを更新
3. **テスト実行**: 各 Phase 完了後にビルドとテストを実行
4. **互換性レイヤー**: 必要に応じて古いパスから新しいパスへの re-export を用意

---

## ✅ 受け入れ条件確認

- [ ] src/shared に横断資産がまとまる
- [ ] 機能固有のロジックは features/\* 配下に移る
- [ ] import の型エラーなし
- [ ] ビルド成功
- [ ] 各機能が独立して理解・変更可能
