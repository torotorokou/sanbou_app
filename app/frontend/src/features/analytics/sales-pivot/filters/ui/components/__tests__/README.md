# FilterPanel コンポーネントテスト計画

## Phase 4: テスト追加

### テスト環境セットアップが必要
現在のプロジェクトには `@testing-library/react` がインストールされていないため、
以下のテストファイルを実行するには事前にテスト環境のセットアップが必要です。

```bash
npm install --save-dev @testing-library/react @testing-library/user-event
```

### 作成済みテストファイル

#### 1. CategorySelector.test.tsx
**テスト内容:**
- ✅ 廃棄物/有価物の表示確認
- ✅ 選択状態の正しい反映
- ✅ ボタンクリック時のonChange呼び出し
- ✅ 両方のオプションが表示されること

**カバレッジ:**
- Props受け渡し
- ユーザーインタラクション
- 状態変更ハンドラー

#### 2. ModeSelector.test.tsx
**テスト内容:**
- ✅ 顧客/品名/日付モードの表示確認
- ✅ 各モードの選択状態確認
- ✅ モード変更時のonChange呼び出し
- ✅ すべてのオプションが表示されること

**カバレッジ:**
- 3つのモードの切り替え
- Segmented コンポーネントの挙動
- 型安全性（Mode型）

#### 3. useFilterLayout.test.ts
**テスト内容:**
- ✅ デスクトップレイアウト設定の取得
- ✅ モバイルレイアウト設定の取得
- ✅ レスポンシブ分岐の正しい動作
- ✅ 各グリッド設定値の妥当性確認

**カバレッジ:**
- useResponsiveフックのモック
- xl以上/未満でのレイアウト分岐
- グリッド設定の整合性

### 今後追加すべきテスト

#### TopNSortControls.test.tsx
- TopN選択（10/20/50/All）の動作確認
- ソートキー選択の動作確認
- 昇順/降順切り替えの動作確認
- sortKeyOptionsのレンダリング確認

#### PeriodSelector.test.tsx
- 月次/日次切り替えの動作確認
- 単一/期間切り替えの動作確認
- DatePickerの表示/非表示ロジック
- 日付選択時のonChange呼び出し
- 複雑な条件分岐のテスト

#### RepFilterSelector.test.tsx
- 営業選択Selectの動作確認
- 全営業表示ボタンの動作確認
- クリアボタンの動作確認
- 絞り込みフィルタSelectの動作確認
- モード切り替えによるフィルタラベル変更

#### FilterPanel.test.tsx（統合テスト）
- すべての子コンポーネントが正しくレンダリングされること
- レスポンシブレイアウトの切り替え確認
- Props伝播の確認
- デスクトップ/モバイルでの表示切り替え

### テスト実行方法（セットアップ後）

```bash
# 全テスト実行
npm test

# 特定ファイルのみ
npm test CategorySelector.test.tsx

# カバレッジ付き
npm test -- --coverage
```

### テストカバレッジ目標

| コンポーネント | 目標カバレッジ | 優先度 |
|--------------|-------------|-------|
| CategorySelector | 100% | 高 |
| ModeSelector | 100% | 高 |
| TopNSortControls | 90%+ | 中 |
| PeriodSelector | 85%+ | 中 |
| RepFilterSelector | 90%+ | 中 |
| useFilterLayout | 100% | 高 |
| FilterPanel | 80%+ | 低 |

### 実装済みテストのポイント

1. **単一責任の原則に沿ったテスト**
   - 各コンポーネントの責務のみをテスト
   - 子コンポーネントの実装詳細に依存しない

2. **ユーザー中心のテスト**
   - userEvent使用でより実際のユーザー操作に近い
   - screen.getByText等でアクセシビリティも考慮

3. **型安全性**
   - TypeScript型定義を活用
   - モック関数の型推論も適切に設定

4. **モック戦略**
   - useResponsiveは外部依存なのでモック化
   - Ant Designコンポーネントは実装をそのまま使用
