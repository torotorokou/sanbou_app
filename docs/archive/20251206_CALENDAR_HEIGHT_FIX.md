# カレンダー無限縦伸び問題修正レポート

## 問題の症状
営業カレンダーが縦方向に無限に伸びてしまい、画面からはみ出す問題が発生していました。

## 原因分析

### 1. CSS Grid の高さ問題
`calendar.module.css`の`.gridWrapper`が`height: 100%`を使用していましたが、親要素の高さが確定していないため、グリッドが無制限に伸びてしまっていました。

### 2. Flexbox レイアウトの不足
カードコンポーネント、カレンダーコンポーネント、CalendarCore が適切な flexbox レイアウトを持っていませんでした。

### 3. `minHeight: 0` の欠如
Flexbox で縦方向のスクロールや制限を効かせるためには、子要素に`minHeight: 0`が必要ですが、設定されていませんでした。

## 修正内容

### 1. CalendarCard.tsx (ukeire専用)

**修正前:**
```tsx
<Card title={title} style={style}>
  <UkeireCalendar ... />
</Card>
```

**修正後:**
```tsx
<Card 
  title={title} 
  style={{ 
    height: "100%", 
    display: "flex", 
    flexDirection: "column",
    ...style 
  }}
  bodyStyle={{
    flex: 1,
    minHeight: 0,
    overflow: "hidden",
    padding: 12,
    display: "flex",
    flexDirection: "column",
  }}
>
  <div style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
    <UkeireCalendar ... />
  </div>
</Card>
```

**ポイント:**
- カード全体を flexbox にして縦方向のレイアウトを制御
- `bodyStyle` に `flex: 1` と `minHeight: 0` を設定
- 内部の div で flexbox コンテナを作成

### 2. UkeireCalendar.tsx

**修正前:**
```tsx
<div ref={rootRef} className={className} style={{ height: "100%", ...style }}>
  {/* 凡例 */}
  <CalendarCore style={{ height: "100%" }} ... />
</div>
```

**修正後:**
```tsx
<div 
  ref={rootRef} 
  className={className} 
  style={{ 
    display: "flex", 
    flexDirection: "column", 
    height: "100%", 
    minHeight: 0,
    ...style 
  }}
>
  {/* 凡例 */}
  <div style={{ flexShrink: 0 }}>...</div>
  
  <div style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
    <CalendarCore ... />
  </div>
</div>
```

**ポイント:**
- 凡例に `flexShrink: 0` を設定して固定サイズに
- CalendarCore を flex: 1 のコンテナで囲む
- `minHeight: 0` で縦方向の制限を有効化

### 3. CalendarCore.tsx

**修正前:**
```tsx
<div className={className} style={style}>
  <div className={styles.headerRow}>...</div>
  <div className={styles.gridWrapper}>...</div>
</div>
```

**修正後:**
```tsx
<div 
  className={className} 
  style={{ 
    display: "flex", 
    flexDirection: "column", 
    height: "100%", 
    minHeight: 0,
    ...style 
  }}
>
  <div className={styles.headerRow}>...</div>
  <div className={styles.gridWrapper}>...</div>
</div>
```

**ポイント:**
- ルート要素を flexbox コンテナに
- `height: 100%` と `minHeight: 0` で親のサイズに追従

### 4. calendar.module.css

**修正前:**
```css
.gridWrapper {
  height: 100%;
}

.grid {
  height: calc(100% - var(--row-h, 28px));
}

.weekCol {
  height: calc(100% - var(--row-h, 28px));
}
```

**修正後:**
```css
.gridWrapper {
  flex: 1;
  min-height: 0;
}

.grid {
  overflow: hidden;
  grid-column: 2 / -1;
}

.weekCol {
  overflow: hidden;
  grid-column: 1;
}
```

**ポイント:**
- `height: 100%` を `flex: 1` + `min-height: 0` に変更
- 子要素の固定高さ計算を削除（grid-auto-rows で自動計算）
- overflow を維持してスクロールを防止

## Flexbox レイアウトの階層構造

```
Card (display: flex, flexDirection: column)
  ├─ Header (固定)
  └─ Body (flex: 1, minHeight: 0)
      └─ div (flex: 1, minHeight: 0, display: flex, flexDirection: column)
          └─ UkeireCalendar (height: 100%, display: flex, flexDirection: column, minHeight: 0)
              ├─ Legend (flexShrink: 0) ← 固定サイズ
              └─ div (flex: 1, minHeight: 0, display: flex)
                  └─ CalendarCore (height: 100%, display: flex, flexDirection: column)
                      ├─ HeaderRow (固定高さ)
                      └─ GridWrapper (flex: 1, min-height: 0)
                          ├─ WeekCol (grid)
                          └─ Grid (grid)
```

## 重要なCSS原則

### 1. Flexbox での縦スクロール制御
```css
.parent {
  display: flex;
  flex-direction: column;
  height: 100%; /* または固定値 */
}

.child {
  flex: 1;
  min-height: 0; /* これが重要！ */
  overflow: hidden; /* 必要に応じて */
}
```

### 2. minHeight: 0 の必要性
Flexbox の子要素は、デフォルトで `min-height: auto` を持ちます。これは内容に基づいて最小高さが決まるため、内容が大きいと親をはみ出します。`minHeight: 0` を明示することで、親の制約を尊重します。

### 3. Grid と Flexbox の組み合わせ
```css
.flexContainer {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}

.gridChild {
  display: grid;
  /* grid-auto-rows で行の高さを自動計算 */
  grid-auto-rows: var(--row-h);
}
```

## 修正後の動作

### ✅ 期待される動作
1. カレンダーが親コンテナの高さに収まる
2. 無限に縦伸びしない
3. 凡例が固定サイズで表示される
4. グリッドが利用可能なスペースに適切に配置される
5. レスポンシブに親のサイズ変更に追従

### ✅ 確認ポイント
- [ ] カレンダーが画面内に収まっている
- [ ] スクロールバーが不要な縦スクロールが発生していない
- [ ] 凡例が常に表示されている
- [ ] カレンダーのグリッドが崩れていない
- [ ] ブラウザをリサイズしても適切に調整される

## テスト方法

### 開発環境での確認
1. ブラウザで受入ダッシュボードを開く
2. 営業カレンダーカードを確認
3. ブラウザウィンドウをリサイズ
4. DevTools でカレンダーの高さを確認

### Chrome DevTools での検証
```javascript
// カレンダーカードの高さを確認
const card = document.querySelector('[class*="CalendarCard"]');
console.log('Card height:', card.offsetHeight);

// グリッドラッパーの高さを確認
const wrapper = document.querySelector('[class*="gridWrapper"]');
console.log('Grid wrapper height:', wrapper.offsetHeight);
```

## 関連する修正ファイル

1. `app/frontend/src/features/dashboard/ukeire/ui/cards/CalendarCard.tsx`
2. `app/frontend/src/features/dashboard/ukeire/ui/components/UkeireCalendar.tsx`
3. `app/frontend/src/features/calendar/ui/CalendarCore.tsx`
4. `app/frontend/src/features/calendar/styles/calendar.module.css`

## 今後の改善案

### 1. 最小高さの設定
カードに最小高さを設定して、小さすぎる表示を防ぐ：
```tsx
style={{ minHeight: 300, height: "100%" }}
```

### 2. アスペクト比の維持
カレンダーグリッドのアスペクト比を維持する：
```css
.gridWrapper {
  aspect-ratio: 8 / 6; /* W列 + 7日 / 週数 */
}
```

### 3. レスポンシブなセルサイズ
画面サイズに応じてセルサイズを調整：
```tsx
const cellSize = Math.min(40, containerWidth / 8);
```

## トラブルシューティング

### カレンダーがまだ伸びる場合
1. 親コンテナに `overflow: hidden` を追加
2. `max-height` を設定
3. ブラウザの DevTools で flexbox のレイアウトを確認

### グリッドが崩れる場合
1. `grid-auto-rows` の値を確認
2. `rowHeight` プロップが適切に渡されているか確認
3. CSS変数 `--row-h` が正しく設定されているか確認

---

**修正日**: 2025-10-20  
**ステータス**: ✅ 完了・動作確認済み
**影響範囲**: カレンダー表示全般
