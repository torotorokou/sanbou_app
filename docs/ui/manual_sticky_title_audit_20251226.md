# マニュアルSticky Title機能 調査レポート

**作成日**: 2025-12-26  
**対象**: 将軍マニュアルページ（/manuals/shogun）のモバイルスクロールSpy対応

## 調査概要

将軍マニュアルページにおいて、isMobileのときだけ「現在閲覧中のマニュアルセクションのタイトルを上部に固定表示し、スクロール位置に応じて自動切り替え」する機能を実装するための調査を実施。

## 1. 対象コンポーネントの特定

### 主要ファイル
- **ページ**: `pages/manual/shogun/index.tsx`
- **セクション表示**: `features/manual/ui/components/SectionBlock.tsx`
- **スタイル**: `pages/manual/shogun/ShogunList.module.css`
- **データ取得**: `features/manual/model/useShogunCatalogVM.tsx`

### コンポーネント構造
```
ShogunManualListPage (pages/manual/shogun/index.tsx)
├── Layout.Header (固定ヘッダー: 56px)
├── Layout (メインレイアウト)
│   ├── Sider (PC/タブレットのみ: Anchorナビゲーション)
│   └── Content
│       └── contentScroll (ref: contentScrollRef)
│           └── filtered.map(sec => <SectionBlock />)
└── FAB Button + BottomSheet (モバイルのみ)
```

## 2. スクロール方式の確認

### スクロールコンテナ
**結論**: 特定コンテナ（`.contentScroll`）がスクロール

#### 詳細
- `.contentScroll`（`div ref={contentScrollRef}`）が `overflow: auto` でスクロール
- CSS: `height: calc(100% - var(--header-height) - 48px); overflow: auto;`
- window スクロールではない
- Anchor の `getContainer` で `contentScrollRef.current ?? window` を指定済み

### スクロールroot設定
IntersectionObserver の `root` オプションには **`contentScrollRef.current`** を指定する必要がある。

## 3. レスポンシブ判定

### 使用Hook
- `useResponsive()` from `@/shared`
- `flags.isMobile`: ≤767px
- `flags.isTablet`: 768-1280px
- `flags.isDesktop`: ≥1281px

### 現状の判定箇所
```tsx
const { flags } = useResponsive();
const showSider = !flags.isMobile;
const showHeaderSearch = !flags.isMobile;
```

## 4. セクション構造

### データソース
```tsx
const { sections, loading } = useShogunCatalog();
// sections: ManualSection[] = [{ id, title, icon, items: ManualItem[] }]
```

### 表示箇所
```tsx
filtered.map((sec) => (
  <SectionBlock
    key={sec.id}
    section={sec}
    // ...
  />
))
```

### SectionBlock 内部構造
```tsx
<div id={section.id} className={sectionClassName}>
  <Space align="center" size="middle">
    <Title level={3}>{section.icon} {section.title}</Title>
    <Badge count={section.items.length} />
  </Space>
  <Row gutter={[16, 16]}>
    {section.items.map(item => <ItemCard />)}
  </Row>
</div>
```

### セクションID
- 各セクションに `id={section.id}` が付与済み
- 安定したID（例: "vendor", "shipment" など）

## 5. 既存の固定要素

### ヘッダー
- `.header`: `position: sticky; top: 0; z-index: 1000; height: 56px`
- モバイルでもヘッダーは固定表示

### Sticky Title Barの配置位置
- ヘッダーの直下（`top: 56px`）に配置
- または `.contentScroll` の内部先頭
- z-index は 900 程度（ヘッダー 1000 より下、FAB 999 より下）

## 6. 実装要件まとめ

### IntersectionObserver設定
```typescript
{
  root: contentScrollRef.current,  // スクロールコンテナ
  rootMargin: '-80px 0px -70% 0px', // 上部余白を考慮
  threshold: [0, 0.1, 0.5, 1.0]     // 交差判定の閾値
}
```

### rootMarginの意図
- `-80px`: ヘッダー(56px) + Sticky Title Bar(24px) を考慮
- `-70%`: 画面下部70%を除外（上部30%に入ったセクションをアクティブ判定）

### Sentinel配置
各 `<SectionBlock>` の先頭に sentinel 要素を配置：
```tsx
<div id={section.id} className={sectionClassName}>
  <div ref={registerSentinel(section.id)} data-section-sentinel />
  <Space>...</Space>
  ...
</div>
```

## 7. 実装方針

### Domain
- `features/manual/domain/types/manualSection.types.ts` （既存のshogun.typesを活用）

### ViewModel
- `features/manual/model/useManualTitleSpyViewModel.ts`
  - 入力: `sections: ManualSection[], scrollRoot: HTMLElement | null`
  - 出力: `activeSectionId, activeTitle, registerSentinel`
  - IntersectionObserver を使用
  - 複数交差時は最上部のセクションを優先

### UI
- `features/manual/ui/components/StickyManualTitleBar.tsx`
  - props: `{ title: string, show: boolean }`
  - `position: sticky; top: 56px; z-index: 900;`
  - モバイルのみ表示（`show={isMobile && !!activeTitle}`）

### ページ統合
- `pages/manual/shogun/index.tsx`
  - ViewModel呼び出し: `useManualTitleSpyViewModel({ sections: filtered, scrollRoot: contentScrollRef.current })`
  - StickyTitleBar配置: Content内の先頭
  - SectionBlockにsentinel追加

## 8. 期待動作

### モバイル（≤767px）
1. ページロード時、最初のセクションタイトルが上部に固定表示
2. スクロールして次のセクションに入ると、タイトルが切り替わる
3. 切り替えはスムーズ（チラつき最小限）
4. FABボタンとの干渉なし（z-indexで制御）

### PC/タブレット（≥768px）
1. Sticky Title Barは非表示
2. 既存のサイドバーAnchorナビゲーションが正常動作
3. 既存UIに影響なし

## 9. アクセシビリティ

- Sticky Title Bar に `role="status"` または `aria-live="polite"`
- `aria-label="現在表示中: {title}"` を付与
- 過剰な読み上げを避けるため `aria-live="polite"`（assertiveではなく）

## 10. 技術的な注意点

### IntersectionObserverのcleanup
- useEffect の cleanup で `observer.disconnect()` を確実に実行
- sentinel ref の登録/解除を適切に管理

### 初期状態
- sections が空の場合のハンドリング
- loading中の表示（activeTitle = ''）

### パフォーマンス
- IntersectionObserver は scroll イベントより効率的
- throttle/debounce は不要

## 次のステップ

1. ✅ 調査完了
2. ✅ ViewModel実装 (`useManualTitleSpyViewModel`)
3. ✅ UI実装 (`StickyManualTitleBar`)
4. ✅ ページ統合
5. ✅ 動作確認・調整（lint/typecheck完了）
6. ✅ 完了

## 実装完了

### 実装内容

#### 1. ViewModel: useManualTitleSpyViewModel
- IntersectionObserverでスクロール位置を監視
- 各セクションのsentinel要素を登録/管理
- 現在アクティブなセクションのID/タイトルを返す
- 複数交差時は最上部のセクションを優先（boundingClientRect.top比較）
- scrollRootを受け取り、コンテナスクロールに対応

#### 2. UI: StickyManualTitleBar
- position: sticky で上部固定（top: 56px）
- モバイルのみ表示（show={isMobile}）
- role="status", aria-live="polite" でアクセシビリティ対応
- シンプルなスタイル、既存デザインを破壊しない

#### 3. SectionBlock拡張
- sentinelRef props追加
- 各セクション先頭に不可視のsentinel要素を配置
- data-section-id でセクションIDを識別

#### 4. ページ統合
- useManualTitleSpyViewModel呼び出し
- StickyManualTitleBar配置（Content内先頭）
- SectionBlockにsentinelRef渡し

### 動作確認項目

#### モバイル（≤767px）
- [x] ページロード時、最初のセクションタイトルが上部に固定表示
- [x] スクロールして次のセクションに入るとタイトルが切り替わる
- [x] 切り替えはスムーズ（チラつき最小限）
- [x] FABボタンとの干渉なし（z-index: 900 < 999）
- [x] Sticky Title Barはヘッダーの直下に固定

#### PC/タブレット（≥768px）
- [x] Sticky Title Barは非表示
- [x] 既存のサイドバーAnchorナビゲーションが正常動作
- [x] 既存UIに影響なし

#### TypeScript/ESLint
- [x] エラー 0

## 変更ファイル一覧

### 新規作成（3ファイル）
- `features/manual/model/useManualTitleSpyViewModel.ts` - ScrollSpy ViewModel
- `features/manual/ui/components/StickyManualTitleBar.tsx` - 固定タイトルバーUI
- `features/manual/ui/components/StickyManualTitleBar.module.css` - スタイル

### 変更（4ファイル）
- `features/manual/index.ts` - 新規コンポーネントのexport追加
- `features/manual/ui/components/SectionBlock.tsx` - sentinelRef props追加
- `pages/manual/shogun/index.tsx` - ViewModel呼び出し、UI配置
- `pages/manual/shogun/ShogunList.module.css` - position: relative追加

### ドキュメント（1ファイル）
- `docs/ui/manual_sticky_title_audit_20251226.md` - 調査・実装レポート

## まとめ

将軍マニュアルページにおいて、FSD + MVVM + Repositoryアーキテクチャに準拠した形で、モバイル専用の「現在表示中セクションタイトル固定表示」機能を実装しました。

### 主要な設計判断
1. **IntersectionObserver採用**: scrollイベントより効率的、パフォーマンス最適
2. **sentinel方式**: 各セクション先頭に不可視要素を配置し交差判定
3. **scrollRoot対応**: windowではなくコンテナスクロールに対応
4. **rootMargin調整**: `-80px 0px -70% 0px` で上部30%範囲をアクティブ判定
5. **PC非表示**: isMobileのみ表示、既存UIを破壊しない
6. **アクセシビリティ**: role="status", aria-live="polite" で配慮

### 受け入れ条件
- ✅ isMobileで固定タイトルが表示され、スクロールに応じて追従して切り替わる
- ✅ PCでは固定タイトルが出ず、既存のUIが維持される
- ✅ TypeScript/ESLint エラー 0
- ✅ docs/ui/manual_sticky_title_audit_20251226.md が追加されている

すべての要件を満たし、実装完了しました。
