# Webアプリ開発 共通ルール（フロントエンド版）
- ファイル名: 20251127_webapp_development_conventions_frontend.md
- 日付: 2025-11-27
- 対象: React + TypeScript フロントエンド全般

---

## 1. 基本方針

- 言語: **TypeScript + React**
- 構成:
  - **Feature-Sliced Design (FSD)**
  - **MVVM（Hooks = ViewModel）**
  - **Repository パターン**（HTTP アダプタを features 側で抽象化）
- 目的:
  - 機能単位でコードを整理し、責務を明確にする
  - フロントとバックエンドの責務分離（画面側にビジネスロジックを持たせない）

---

## 2. ディレクトリ構成ルール

### 2-1. 全体構成（例）

```text
src/
  pages/
    analytics/
      SalesTreePage.tsx             # 画面骨組み・ルーティング
    report/
      ReportDailyPage.tsx
  features/
    analytics/
      sales-pivot/
        ui/                         # 状態レスの View コンポーネント
        model/
          useSalesPivotViewModel.ts # MVVM: 画面状態・イベント集約
          types.ts                  # DTO / ViewModel 型定義
        domain/                     # 必要に応じたドメインオブジェクト
        ports/                      # Repository インターフェース（抽象）
        infrastructure/
          salesPivot.repository.ts  # Repository 実装（HTTP + DTO整形）
    report/
      ...
  shared/
    infrastructure/http/            # 共通 HTTP クライアント (coreApi など)
  hooks/ui/                         # 共通 UI hooks（レスポンシブ等）
  constants/                        # カラー・ブレイクポイントなど
```

### 2-2. 役割分担

- **pages/**  
  - 画面の骨組み・レイアウト・ルーティングのみを担当
  - 画面状態やビジネスロジックは ViewModel に委譲
  - API 呼び出しや Repository の利用は禁止

- **features/<feature>/ui/**  
  - 完全に **状態レス**の View コンポーネント
  - props で値・コールバックを受け取り、表示だけに専念
  - `useState` や API 呼び出しは原則禁止

- **features/<feature>/model/**  
  - `useXxxViewModel` で画面の状態・イベントを集約
  - Repository（ports）を呼び出してデータ取得・更新を行う
  - UI で扱いやすい形にデータを整形する
  - ビジネスロジックは極力ここか domain に寄せる

- **features/<feature>/domain/**  
  - その機能専用の軽量ドメインオブジェクト・値オブジェクト
  - 値の検証・変換ロジックなどをまとめる
  - 外部 I/O（HTTP・localStorage 等）は行わない

- **features/<feature>/ports/**  
  - Repository のインターフェース（抽象）を定義
  - `interface SalesPivotRepository { ... }` のように宣言のみ
  - 実装詳細（axios/fetch 等）に依存しない

- **features/<feature>/infrastructure/**  
  - Repository インターフェースの実装
  - 共通 HTTP クライアント（`coreApi` など）を利用して通信
  - DTO（APIレスポンス）⇔ Domain / ViewModel 型の変換を担当

- **shared/**  
  - 複数 feature から共有される UI コンポーネント・hooks・定数等
  - 特定機能に強く依存するものは置かない

---

## 3. コーディング規約（フロント）

### 3-1. 命名規則

- 変数・関数・プロパティ: **camelCase**
  - 例: `repId`, `customerName`, `createdAt`
- 型名・コンポーネント名: **PascalCase**
  - 例: `SalesPivotBoard`, `ReportDailyPageProps`
- ファイル名:
  - コンポーネント: `SalesPivotBoard.tsx`
  - hooks: `useSalesPivotViewModel.ts`
  - 型定義: `types.ts`（feature 内で共通）

### 3-2. 型と安全性

- TypeScript の型定義は必須
- `any` の使用は禁止（やむを得ない場合は TODO コメントを付ける）
- API レスポンスは **専用の型（interface）** を定義し、Repository で変換する

### 3-3. API 通信

- 画面（pages/ui）から `fetch` / `axios` を直接呼ばない
- 必ず Repository（ports + infrastructure）経由で API を呼び出す

```ts
// NG (pages 直で axios)
const res = await axios.get('/api/sales');

// OK (ViewModel から Repository)
const data = await salesPivotRepository.fetchSummary(params);
```

---

## 4. レイアウト・UI 共通ルール

- レイアウト:
  - 共通の breakpoints（`constants/breakpoints.ts`）を使用
  - PC / タブレット / スマホでの表示切替は共通 hooks（`useResponsive` 等）を使う
- カラー:
  - PALETTE 定義を利用し、マジックナンバーのカラーコードは使わない
- コンポーネント:
  - 再利用可能な UI は `shared/ui`（または既存方針に従う）へ切り出す

---

## 5. エラーハンドリング・メッセージ

- API エラーは ViewModel で受け取り、UI には「文言」と「状態」を渡す
- ユーザー向けメッセージは日本語で分かりやすく
  - 例: 「データの取得に失敗しました。時間をおいて再度お試しください。」

---

## 6. ドキュメントとの関係

- フロントエンドで使用する API エンドポイント・パラメータは、必要に応じて `docs/` 以下にまとめる
- カラム名・フィールド名などは `column_naming_dictionary.md` のルールに従う（※DB/バックエンド側ドキュメントを参照）
