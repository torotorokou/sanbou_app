# Feature Flags (機能フラグ) ガイド

> **最終更新**: 2025-12-26

## 目的

Feature Flags は、途中機能を本番から隔離しつつ、dev/stg 環境では有効化できる仕組みです。

### なぜ必要か？

- **途中機能の隔離**: main/dev にマージされても、本番ユーザーには見えない
- **複数タスクの並行開発**: dev ブランチに複数の途中機能が混在しても安全
- **段階的リリース**: stg で検証後、フラグを ON にして本番公開
- **緊急時の切り戻し**: 問題発生時はフラグ OFF で即座に非公開化

## 重要な変更（v2.0 - 2025-12-26）

### 未完成モーダルからの移行

従来の「未完成モーダルで追い返す」実装を廃止し、Feature Flags ベースの安全な隔離方式に統一しました。

**Before（廃止）:**

```tsx
// ❌ 旧実装: モーダルで追い返す
const [showModal, setShowModal] = useState(false);
useEffect(() => {
  setShowModal(true);
}, []);
<UnimplementedModal visible={showModal} onClose={() => navigate("/")} />;
```

**After（推奨）:**

```tsx
// ✅ 新実装: ルート未接続 + インライン準備中パネル
// AppRoutes.tsx - ページ単位
{
  isFeatureEnabled("FACTORY_REPORT") && (
    <Route path="/report/factory" element={<FactoryPage />} />
  );
}

// DetailPage.tsx - 部品単位
{
  showManualVideo ? (
    <VideoPlayer src={url} />
  ) : (
    <ComingSoonPanel title="動画機能 準備中" />
  );
}
```

### 2種類の未完成パターン

| パターン         | 用途                       | 実装方法        | ユーザー体験                           |
| ---------------- | -------------------------- | --------------- | -------------------------------------- |
| **ページ未完成** | ページ全体が未完成         | ルート未接続    | ナビに出ない、URL直打ちで404           |
| **部品未完成**   | ページ内の特定機能が未完成 | ComingSoonPanel | ページは使える、該当部品のみ準備中表示 |

### 廃止された機能

- `UnimplementedModal` - モーダルでトップページに戻す実装を廃止
- ページ読み込み時の自動モーダル表示 - 削除

## 基本概念

### 「見えない」だけでなく「アクセス不能」

Feature Flags OFF の場合:

1. **ルート未接続**: 該当パスは `Routes` に含まれない → URL直打ちでも404
2. **UI非表示**: サイドバー/ナビ/ポータルカードにリンクが表示されない
3. **コード分離**: lazy loading で、OFF の機能はバンドルに含まれない

## ファイル構成

```
src/shared/
├── config/
│   ├── featureFlags.ts     # フラグ定義・判定関数
│   └── index.ts            # barrel export
└── hooks/
    └── useFeatureFlags.ts  # ViewModel Hook

src/app/
├── routes/
│   ├── routes.ts           # パス定数（実験的パス含む）
│   └── AppRoutes.tsx       # ルート定義（フラグで条件分岐）
└── navigation/
    └── sidebarMenu.tsx     # サイドバーメニュー（フラグで hidden 制御）

src/pages/
└── experimental/           # 実験的ページを配置
    └── NewReportPage.tsx   # サンプル実装
```

## フラグの追加手順

### Step 1: フラグ定義を追加

[src/shared/config/featureFlags.ts](../src/shared/config/featureFlags.ts) を編集:

```typescript
export const FEATURE_FLAGS = {
  // ... 既存のフラグ

  /**
   * 新しい機能の説明
   * 環境変数: VITE_FF_MY_NEW_FEATURE=true
   */
  MY_NEW_FEATURE: "MY_NEW_FEATURE",
} as const;
```

### Step 2: 環境変数を追加

各 env ファイルに追加:

```bash
# env/.env.local_dev (開発: ON)
VITE_FF_MY_NEW_FEATURE=true

# env/.env.vm_stg (ステージング: ON)
VITE_FF_MY_NEW_FEATURE=true

# env/.env.vm_prod (本番: OFF)
VITE_FF_MY_NEW_FEATURE=false
```

### Step 3: ルート未接続を実装

[src/app/routes/routes.ts](../src/app/routes/routes.ts) にパスを追加:

```typescript
export const ROUTER_PATHS = {
  // ... 既存のパス

  /** 新機能 (VITE_FF_MY_NEW_FEATURE=true で有効) */
  MY_NEW_FEATURE: "/experimental/my-new-feature",
};
```

[src/app/routes/AppRoutes.tsx](../src/app/routes/AppRoutes.tsx) で条件分岐:

```tsx
import { isFeatureEnabled } from "@/shared";

// lazy load (フラグ OFF ならバンドルされない)
const MyNewFeaturePage = lazy(() =>
  import("@/pages/experimental").then((m) => ({ default: m.MyNewFeaturePage })),
);

// ルート定義内
{
  isFeatureEnabled("MY_NEW_FEATURE") && (
    <Route path={ROUTER_PATHS.MY_NEW_FEATURE} element={<MyNewFeaturePage />} />
  );
}
```

### Step 4: UI 露出を制御

サイドバーの場合、[src/app/navigation/sidebarMenu.tsx](../src/app/navigation/sidebarMenu.tsx) で `hidden` を制御:

```tsx
{
  key: ROUTER_PATHS.MY_NEW_FEATURE,
  icon: <SomeIcon />,
  label: <Link to={ROUTER_PATHS.MY_NEW_FEATURE}>新機能</Link>,
  // Feature Flag OFF なら非表示
  hidden: !isFeatureEnabled('MY_NEW_FEATURE'),
}
```

ViewModel を使う場合:

```tsx
// コンポーネント内
const { isEnabled } = useFeatureFlags();
const showMyNewFeature = isEnabled("MY_NEW_FEATURE");

// JSX
{
  showMyNewFeature && (
    <NavLink to={ROUTER_PATHS.MY_NEW_FEATURE}>新機能</NavLink>
  );
}
```

## 環境ごとの推奨設定

| 環境        | フラグ設定 | 用途                         |
| ----------- | ---------- | ---------------------------- |
| `local_dev` | ON         | 開発者が新機能を実装・テスト |
| `vm_stg`    | ON         | ステージング環境で検証       |
| `vm_prod`   | OFF        | 本番環境は安定版のみ         |

## 実装パターン

### パターン A: ページ未完成（ルート未接続）

ページ全体が未完成の場合、フラグ OFF でルートを生成しない。

```tsx
// 1. featureFlags.ts にフラグを追加
export const FEATURE_FLAGS = {
  FACTORY_REPORT: 'FACTORY_REPORT',
} as const;

// 2. AppRoutes.tsx でルート未接続
{isFeatureEnabled('FACTORY_REPORT') && (
  <Route path={ROUTER_PATHS.REPORT_FACTORY} element={<ReportFactoryPage />} />
)}

// 3. sidebarMenu.tsx でナビ非表示
{
  key: ROUTER_PATHS.REPORT_FACTORY,
  label: <Link to={ROUTER_PATHS.REPORT_FACTORY}>工場帳簿</Link>,
  hidden: !isFeatureEnabled('FACTORY_REPORT'),
}

// 4. env ファイルで制御
// env/.env.local_dev
VITE_FF_FACTORY_REPORT=true  // 開発: ON

// env/.env.vm_prod
VITE_FF_FACTORY_REPORT=false // 本番: OFF
```

### パターン B: 部品未完成（ComingSoonPanel）

ページ内の特定機能が未完成の場合、準備中パネルを表示。

```tsx
// 1. ViewModel で Feature Flag を判定
const { showManualVideo } = useFeatureFlags();

// 2. UI で条件分岐（モーダルではなくインライン）
<div className={styles.videoPane}>
  {showManualVideo ? (
    <VideoPane src={item.videoUrl} />
  ) : (
    <ComingSoonPanel
      title="動画機能 準備中"
      description="動画再生機能は現在準備中です。近日中に公開予定ですので、今しばらくお待ちください。"
      type="info"
    />
  )}
</div>;
```

### パターン C: 開発中警告バナー（WipNotice）

ページ全体は使えるが、開発中であることを示す場合。

```tsx
import { WipNotice } from "@/features/wip-notice";

<WipNotice
  show={true}
  message="開発中の機能です"
  description="この機能は現在開発中です。一部機能が正常に動作しない可能性があります。"
/>;
```

## 実例

### 実装例 1: 工場帳簿ページ（ページ未完成）

**状況**: 工場帳簿ページ全体が開発中

**実装**:

- `VITE_FF_FACTORY_REPORT=false` で本番では非公開
- ルート未接続により URL 直打ちでも 404
- サイドバーにリンクが表示されない

**変更箇所**:

- [src/shared/config/featureFlags.ts](../../src/shared/config/featureFlags.ts) - フラグ定義
- [src/app/routes/AppRoutes.tsx](../../src/app/routes/AppRoutes.tsx) - ルート制御
- [src/app/navigation/sidebarMenu.tsx](../../src/app/navigation/sidebarMenu.tsx) - ナビ制御
- [env/.env.vm_prod](../../../../env/.env.vm_prod) - 本番OFF設定

### 実装例 2: マニュアル動画機能（部品未完成）

**状況**: マニュアルページは動作するが、動画機能のみ未完成

**実装**:

- `VITE_FF_MANUAL_VIDEO=false` で動画セクションに準備中パネル
- ページ自体は正常にアクセス可能
- ユーザーは他の機能（フローチャート等）を利用できる

**変更箇所**:

- [src/pages/manual/shogun/DetailPage.tsx](../../src/pages/manual/shogun/DetailPage.tsx) - 動画セクション制御

### 実装例 3: 開発中ダッシュボード（WipNotice）

**状況**: ダッシュボードは使えるが、一部データが未完成

**実装**:

- ページトップに開発中警告バナーを表示
- ユーザーに「開発中」であることを明示
- 機能は正常に使える

**変更箇所**:

- [src/pages/dashboard/ukeire/InboundForecastDashboardPage.tsx](../../src/pages/dashboard/ukeire/InboundForecastDashboardPage.tsx)

## トラブルシューティング

### Q: 従来の UnimplementedModal を使っている箇所の移行方法は？

**A: 以下の手順で移行してください**

1. **ページ単位の未完成の場合**:
   - `UnimplementedModal` と `useEffect` による自動表示を削除
   - `VITE_FF_XXX` フラグを定義
   - `AppRoutes.tsx` でルート未接続を実装
   - `sidebarMenu.tsx` でナビ非表示を実装

2. **部品単位の未完成の場合**:
   - `UnimplementedModal` を削除
   - `ComingSoonPanel` を該当セクションに配置
   - `useFeatureFlags()` で表示制御

3. **開発中警告のみの場合**:
   - `UnimplementedModal` を削除
   - `WipNotice` をページトップに配置

### Q: フラグを ON にしたのに反映されない

**A: 再ビルドが必要です**

Vite はビルド時に環境変数を埋め込むため、env ファイルを変更したら:

```bash
# 開発環境
npm run dev  # 再起動

# 本番ビルド
npm run build  # 再ビルド & 再デプロイ
```

### Q: フラグ名を typo したらどうなる？

**A: TypeScript が型エラーを出します**

`isFeatureEnabled('TYPO')` は型エラーになります:

```
Argument of type '"TYPO"' is not assignable to parameter of type 'FeatureFlagKey'.
```

### Q: 本番で一時的にフラグを ON にしたい

**A: env ファイルを変更して再デプロイ**

```bash
# env/.env.vm_prod
VITE_FF_NEW_FEATURE=true

# 再ビルド & 再デプロイ
```

### Q: バンドルサイズへの影響は？

**A: 最小限です**

- lazy loading を使用しているため、フラグ OFF の機能はバンドルに含まれません
- `isFeatureEnabled()` は軽量な文字列比較のみ

## 命名規則

| 項目       | 規則                    | 例                           |
| ---------- | ----------------------- | ---------------------------- |
| フラグキー | SCREAMING_SNAKE_CASE    | `NEW_REPORT`, `EXPERIMENTAL` |
| 環境変数   | `VITE_FF_` + キー       | `VITE_FF_NEW_REPORT`         |
| パス       | `/experimental/` prefix | `/experimental/new-report`   |

## セキュリティ考慮

- Feature Flags はクライアントサイドで判定されます
- API 側のアクセス制御は別途実装が必要です
- 機密機能の場合は、バックエンドでも同様のフラグチェックを行ってください

## 参考リンク

- [Vite 環境変数ドキュメント](https://vitejs.dev/guide/env-and-mode.html)
- [Feature-Sliced Design](https://feature-sliced.design/)
