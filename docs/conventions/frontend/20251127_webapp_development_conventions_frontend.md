# Webアプリ開発 共通ルール（フロントエンド版）
- ファイル名: 20251127_webapp_development_conventions_frontend.md
- 日付: 2025-11-27
- 対象: React + TypeScript フロントエンド全般

---

## 1. 基本方針

- 言語: **TypeScript + React**
- 構成:
  - **Feature-Sliced Design (FSD)**  
    - 「機能ごと」にフォルダを分割する
  - **MVVM / VVMC パターン**  
    - View（UI コンポーネント）
    - ViewModel（Hooks = 画面状態＋イベント）
    - Model（domain / ports / infrastructure）
    - Controller（ルーティング・画面遷移）
  - **Repository パターン**  
    - HTTP アダプタを features 側で抽象化し、画面からは直接 HTTP を意識しない
- 目的:
  - 機能単位でコードを整理し、責務を明確にする
  - フロントとバックエンドの責務分離（画面側にビジネスロジックを持たせない）
  - 命名とディレクトリ構造の一貫性を保ち、保守性を高める

---

## 2. ディレクトリ構成ルール

### 2-1. 全体構成（例）

フロントエンド全体の代表的な構成例:

```text
src/
  app/
    router/                         # ルーティング設定（React Router 等）
  pages/
    analytics/
      SalesTreePage.tsx             # 画面の骨組み・ルーティングの着地点
    report/
      ReportDailyPage.tsx
  features/
    analytics/
      salesPivot/
      customerList/
    report/
      reportDaily/
      reportMonthly/
    dashboard/
      ukeire/
      inbound/
    ...
  shared/
    ui/                             # 汎用 UI コンポーネント
      hooks/                        # 共通 UI hooks（レスポンシブ等）
    infrastructure/http/            # 共通 HTTP クライアント (coreApi など)
  constants/                        # カラー・ブレイクポイントなど
```

- `pages/` … 画面単位（ルーティングの終点）  
- `features/` … 機能（feature）単位のモジュール  
- `shared/` … 複数 feature から利用される共通部品  
- `constants/` … カラー・ブレイクポイント・定数類  

**注意:**  
既存構成では `analytics`, `dashboard`, `database`, `manual`, `navi`, `notification`, `report` などが `features` 相当のルートになっている。  
今後は上記方針を「理想形」としつつ、段階的に揃えていく。

### 2-2. 各機能配下（`features/<group>/<feature>/` の例）

```text
src/
  features/
    analytics/
      salesPivot/
        ui/                         # 状態レスの View コンポーネント
          SalesPivotBoard.tsx
          SalesPivotFilterPanel.tsx
        model/                      # ViewModel + 補助 hooks + 型定義
          useSalesPivotVM.ts        # メイン ViewModel
          useMasterData.ts          # 補助 hook
          types.ts                  # ViewModel / DTO 型定義
        domain/                     # 機能専用ドメインオブジェクト
          salesPivot.ts
        ports/                      # Repository インターフェース（抽象）
          SalesPivotRepository.ts
        infrastructure/             # Repository 実装・HTTP アダプタ
          salesPivot.repository.ts
          salesPivot.client.ts      # 必要に応じて
```

- `<group>` … 大きな機能カテゴリ（例: `analytics`, `dashboard`, `report`）
- `<feature>` … その中のサブ機能（例: `salesPivot`, `customerList` など）

※ 既存コードは `model/`, `infrastructure/`, `ports/`, `domain/`, `ui/` ディレクトリを使用。
新規実装・リファクタリング時は以下の役割分担に合わせて統一する。

### 2-3. 役割分担（VVMC との対応）

#### View（V）

- 対応ディレクトリ:
  - `features/<group>/<feature>/ui/`
  - `src/pages/**`（画面の骨組み）
- 役割:
  - 完全に **状態レス**の View コンポーネントを置く
  - props で値・コールバックを受け取り、表示に専念
  - `useState` や API 呼び出しは原則禁止
- 例:
  - `SalesPivotBoard.tsx`
  - `ConditionPanel.tsx`
  - `CustomerComparisonResultCard.tsx`

#### ViewModel（VM）

- 対応ディレクトリ:
  - `features/<group>/<feature>/model/`
- 役割:
  - 画面の状態・イベントを集約する hooks（**`useXxxVM`**）を置く
  - Repository（ports）を呼び出してデータ取得・更新を行う
  - UI で扱いやすい形にデータを整形する
  - 軽いビジネスロジックはここに置いてよい（重いものは domain に寄せる）
  - ViewModel を補助する hooks も同じ `model/` に配置可能
- ファイル命名:
  - `useSalesPivotVM.ts` (ViewModel)
  - `useInboundMonthlyVM.ts` (ViewModel)
  - `useCalendarVM.ts` (ViewModel)
  - `useReportArtifact.ts` (補助 hook)
  - `useCustomerComparison.ts` (補助 hook)

#### Model（M）

- 対応ディレクトリ:
  - `features/<group>/<feature>/model/` - **ViewModel と補助 hooks**
  - `features/<group>/<feature>/domain/` - ドメインロジック
  - `features/<group>/<feature>/ports/` - Repository 抽象
  - `features/<group>/<feature>/infrastructure/` - Repository 実装

1. **model/**
   - 画面の状態・イベント管理を担当する ViewModel hooks（`useXxxVM.ts`）
   - ViewModel を補助する hooks（データ取得、状態管理、計算ロジックなど）
   - 型定義（`types.ts`）や定数も配置可能
   - 例: `useSalesPivotVM.ts`, `useReportArtifact.ts`, `useMasterData.ts`

2. **domain/**
   - 機能専用のドメインオブジェクト・値オブジェクト・サービス
   - 値の検証・変換ロジックなど
   - 外部 I/O（HTTP・localStorage 等）には依存しない

3. **ports/**
   - Repository インターフェース（抽象）を定義
   - 例: `interface SalesPivotRepository { ... }`
   - 実装詳細（axios/fetch 等）に依存しない

4. **infrastructure/**
   - Repository インターフェースの実装
   - 共通 HTTP クライアント（`coreApi` など）を利用して通信
   - DTO（API レスポンス）⇔ Domain / ViewModel 型の変換を担当
   - 既存の `api/` ディレクトリで HTTP アダプタを持っているものは、将来的に `infrastructure/` へ寄せる

#### Controller（C）

- 対応ディレクトリ:
  - `src/app/router/`
  - `src/pages/**`
- 役割:
  - URL とページコンポーネントの結びつけ（ルーティング）
  - 「このページでどの ViewModel を使うか」の選択
  - 極力ビジネスロジックは持たず、画面遷移と構成の制御に限定する

---

## 3. コーディング規約（フロント）

### 3-1. 命名規則

- 変数・関数・プロパティ: **camelCase**
  - 例: `repId`, `customerName`, `createdAt`
- 型名・コンポーネント名: **PascalCase**
  - 例: `SalesPivotBoard`, `ReportDailyPageProps`
- ファイル名:
  - コンポーネント: `SalesPivotBoard.tsx`
  - ViewModel hooks: `useSalesPivotVM.ts`
  - 型定義: `types.ts`（feature 内で共通）
  - Repository 抽象: `SalesPivotRepository.ts`
  - Repository 実装: `salesPivot.repository.ts`

### 3-2. 型と安全性

- TypeScript の型定義は必須
- `any` の使用は禁止（やむを得ない場合は TODO コメントを付ける）
- API レスポンスは **専用の型（interface）** を定義し、Repository で変換する
  - 例:
    - `SalesPivotSummaryResponse`（生レスポンス）
    - `SalesPivotSummary`（ViewModel / Domain 用）

### 3-3. Export / Import スタイル

- **Named Export を推奨** (FSD ベストプラクティス)
  - TypeScript/hooks/utilities: 必ず named export を使用
    ```typescript
    // ✅ Good
    export function useCustomerChurnVM() { ... }
    export const calculateTotal = () => { ... }
    export interface CustomerData { ... }
    ```
  - React コンポーネント: named export を推奨（既存の default export も許容）
    ```typescript
    // ✅ Preferred (新規コード)
    export function CustomerList() { ... }
    
    // ✅ Acceptable (既存コード・互換性)
    export default function CustomerList() { ... }
    ```
- Feature の `index.ts` では明示的な re-export
  ```typescript
  // ✅ Good - 明示的
  export { useCustomerChurnVM } from './model/useCustomerChurnVM';
  export { CustomerList } from './ui/CustomerList';
  
  // ⚠️ 既存コードとの互換性のため許容
  export { default as CustomerList } from './ui/CustomerList';
  ```
- Barrel export (`export *`) は慎重に使用
  - 型定義の場合は許容: `export * from './types'`
  - 実装コードは明示的な export を優先

---

## 4. API 通信ルール

- View（`pages` / `ui`）から `fetch` / `axios` を直接呼ばない
- 必ず Repository（ports + infrastructure）経由で API を呼び出す

```ts
// NG (pages 直で axios)
const res = await axios.get('/api/sales');

// OK (ViewModel から Repository 経由)
const data = await salesPivotRepository.fetchSummary(params);
```

- 共通 HTTP クライアント（`coreApi` など）は `shared/infrastructure/http/` に配置する
- 各 Repository 実装では:
  - `coreApi.get<RawResponse>(...)` などで通信
  - RawResponse → Domain 型 or ViewModel DTO へ変換して返す

---

## 5. レイアウト・UI 共通ルール

- レイアウト:
  - 共通の breakpoints（`constants/breakpoints.ts`）を使用する
  - PC / タブレット / スマホでの表示切替は `shared/ui/hooks/useResponsive` 等の共通 hooks を使う
- カラー:
  - PALETTE 定義（`constants/colors.ts` など）を利用し、マジックナンバーのカラーコードは使わない
- コンポーネント:
  - 再利用可能な UI は `shared/ui` に切り出す  
    （ボタン、カード、モーダル、チャートラッパー等）
  - 特定機能に強く依存する UI は、当該 feature 配下に留める

---

## 6. エラーハンドリング・メッセージ

- API エラーは **ViewModel で受け取る**
  - 例: `errorMessage`, `isNetworkError`, `isLoading` などの状態を用意する
- UI では props として渡された状態に応じてメッセージやローディングを表示する
- ユーザー向けメッセージは日本語で分かりやすく記述する
  - 例: 「データの取得に失敗しました。時間をおいて再度お試しください。」

---

## 7. ドキュメントとの関係

- フロントエンドで使用する API エンドポイント・パラメータは、必要に応じて `docs/` 以下にまとめる
- カラム名・フィールド名などは `column_naming_dictionary.md` のルールに従う（DB/バックエンド側ドキュメントを参照）
- バックエンドの規約（`20251127_webapp_development_conventions_backend.md`）と整合を取ること
  - API のレスポンスフィールドは基本的に DB（mart）のカラム名に合わせた snake_case（バックエンド）
  - フロントでは camelCase に変換して扱う（必要に応じて）

---

## 8. 今後のリファクタリング方針（ガイドライン）

- 既存コードは一気に作り直さず、**触るタイミングで徐々にルールに揃える**
- 特に以下の点を優先する:
  1. ViewModel hooks の命名を `useXxxVM.ts` に統一する ✅ 完了 (Step 1-6)
  2. HTTP 関連の実装を `infrastructure/` に寄せる（`api/` から移動）✅ 完了 (Step 2B-6)
  3. hooks/ ディレクトリを `model/` に統合する ✅ 完了 (Step 13-16)
  4. `application/` ディレクトリを `model/` に統一する ✅ 完了 (Step 7-12)
     - **重要**: FSD 公式では application layer を推奨するが、本プロジェクトでは
       ViewModel + 補助hooks を包含する `model/` に統一する方針を採用済み
  5. View（ui）から直接 HTTP を呼ばない構造にする
  6. 新規コンポーネントで Named Export を使用する（既存は段階的に移行）
  7. `model/`（ViewModel + 補助hooks）と `domain/`（純ロジック）の役割をコメントや README で明示する

### リファクタリング完了状況 (2025-11-29)

- ✅ 全 ViewModel を `useXxxVM.ts` 命名に統一
- ✅ 全 `api/` ディレクトリを `infrastructure/` に移行
- ✅ 全 `application/` ディレクトリを `model/` に統合
- ✅ 全 `hooks/` ディレクトリを `model/` に統合 (Step 18 最終確認完了)
- ✅ FSD アーキテクチャ完全準拠達成
- ✅ Export スタイルガイドライン完全準拠
  - Named Export を推奨として明文化
  - 主要コンポーネント（CalendarCard, InfoTooltip, AnswerViewer）を Named Export に移行
  - Barrel export (`export *`) を最適化（型定義は許容、実装は明示的に）
  - csv-validation と report の index.ts を明示的な export に変更

以上をフロントエンド共通ルールとし、新規実装およびリファクタリング時の基準とする。
