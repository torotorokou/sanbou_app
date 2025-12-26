# 循環依存検知ガイド (madge)

## 📦 ツール概要

`madge` は JavaScript/TypeScript プロジェクトの依存関係を分析し、循環依存を検出するツールです。

## 🎯 目的

FSDアーキテクチャのフォルダ移動時に発生しがちな循環依存を早期に検知し、コードベースの健全性を保ちます。

## 🚀 使い方

### 1. 依存関係グラフの表示

全体の依存関係ツリーを表示します:

```bash
npm run dep:graph
```

**出力例**:

```
src/App.tsx
  src/app/layout/MainLayout.tsx
    src/app/layout/Sidebar.tsx
      src/shared/constants/sidebarMenu.tsx
        src/shared/constants/router.ts
```

### 2. 循環依存の検出（推奨）

循環依存のみを検出します:

```bash
npm run dep:circular
```

**循環がない場合**:

```
✔ No circular dependencies found!
```

**循環がある場合の出力例**:

```
✖ Found 2 circular dependencies!

1) src/features/report/model/report.types.ts > src/features/report/hooks/useReportBase.ts > src/features/report/model/report.types.ts

2) src/pages/manual/ListPage.tsx > src/pages/manual/types.ts > src/pages/manual/ManualModal.tsx > src/pages/manual/ListPage.tsx
```

### 3. 依存関係グラフの画像生成

SVG形式のグラフ画像を生成します（Graphviz必要）:

```bash
npm run dep:image
```

生成されるファイル: `dependency-graph.svg`

**注意**: このコマンドを実行するには `graphviz` が必要です:

```bash
# Ubuntu/Debian
sudo apt-get install graphviz

# macOS
brew install graphviz
```

## 📊 循環依存の読み方

### パターン1: 直接的な相互依存

```
A.tsx > B.tsx > A.tsx
```

- **意味**: A が B をインポートし、B が A をインポートしている
- **修正方法**:
  1. 共通ロジックを `shared/` に抽出
  2. どちらかを上位レイヤーに移動
  3. インターフェースを使って依存を反転

### パターン2: 複数ファイルを経由した循環

```
A.tsx > B.tsx > C.tsx > A.tsx
```

- **意味**: A → B → C → A という依存チェーンができている
- **修正方法**:
  1. 最も基礎的なモジュールを `shared/` に移動
  2. レイヤーの責務を見直す
  3. 型定義を分離する（types.ts）

### パターン3: 型定義の循環

```
types.ts > Component.tsx > types.ts
```

- **意味**: 型定義ファイルとコンポーネントが相互参照
- **修正方法**:
  1. 型定義を分割（基本型 / 拡張型）
  2. 型のみのインポートを使用（`import type`）

## 🔧 FSD層別の修正ガイド

### shared層での循環

```bash
# 検出例
src/shared/utils/helper.ts > src/shared/hooks/useData.ts > src/shared/utils/helper.ts
```

**修正方法**:

- ファイルを分割: `helper.ts` → `helper-core.ts` + `helper-extended.ts`
- より基礎的な関数を別ファイルに移動

### features層での循環

```bash
# 検出例
src/features/report/model/types.ts > src/features/report/hooks/useReport.ts > src/features/report/model/types.ts
```

**修正方法**:

1. hooks と model を明確に分離
2. 型定義を `model/types.ts` に集約
3. hooks では `import type` を使用

### pages層での循環

```bash
# 検出例
src/pages/manual/ListPage.tsx > src/pages/manual/types.ts > src/pages/manual/ManualModal.tsx > src/pages/manual/ListPage.tsx
```

**修正方法**:

1. `ManualModal` を `features/manual/ui/` に移動
2. または `types.ts` を `shared/types/manual.ts` に移動

## 📝 実行手順（ターミナル）

### ステップ1: プロジェクトディレクトリに移動

```bash
cd /home/koujiro/work_env/22.Work_React/sanbou_app/app/frontend
```

### ステップ2: 循環依存をチェック

```bash
npm run dep:circular
```

### ステップ3: 結果の解釈

- ✅ **"No circular dependencies found!"** → OK
- ❌ **"Found X circular dependencies!"** → 修正が必要

### ステップ4: 詳細な依存関係を確認（必要に応じて）

```bash
# 全体のツリー表示
npm run dep:graph

# 特定のファイルのみ
npm run dep:graph -- src/features/report
```

## 🔍 既存のエイリアスコマンド

プロジェクトには既に以下のコマンドも存在します:

```bash
npm run depcheck  # dep:circular と同じ（既存のエイリアス）
```

## 📈 CI/CDへの統合（推奨）

Pull Request作成時に自動チェック:

```yaml
# .github/workflows/dependency-check.yml
name: Dependency Check
on: [pull_request]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - run: npm ci
      - run: npm run dep:circular
```

## 🎨 便利なオプション

### 特定のディレクトリのみチェック

```bash
npm run dep:circular -- src/features
```

### JSONフォーマットで出力

```bash
npx madge --ts-config ./tsconfig.json --json --circular src
```

### 除外パターンを指定

```bash
npx madge --ts-config ./tsconfig.json --exclude ".*\.test\.tsx?" --circular src
```

## ⚠️ よくある問題と解決策

### 問題1: "No circular dependencies found!" だが循環がある気がする

**原因**: TypeScriptパスエイリアス（`@features/`等）が解決できていない
**解決策**: `tsconfig.json` のパス設定を確認

### 問題2: 大量の循環が検出される

**原因**: レイヤー設計が不適切、または型定義の分離不足
**解決策**:

1. FSD層の責務を見直す
2. 型定義を `shared/types/` に集約
3. `import type` を活用

### 問題3: グラフ生成が失敗する

**原因**: Graphvizがインストールされていない
**解決策**:

```bash
sudo apt-get install graphviz  # Ubuntu/Debian
brew install graphviz          # macOS
```

## 📚 参考リンク

- [madge GitHub](https://github.com/pahen/madge)
- [循環依存のベストプラクティス](https://feature-sliced.design/docs/reference/isolation/circular-dependencies)
- [FSD公式ドキュメント](https://feature-sliced.design/)

## 🎯 まとめ

### 日常的な使い方

```bash
# フォルダ移動後、必ずチェック
npm run dep:circular

# 問題があれば詳細確認
npm run dep:graph -- src/features/your-feature
```

### 修正の基本原則

1. **下位レイヤーから上位レイヤーへの依存のみ許可**
   - shared → features → pages → app
2. **共通ロジックは shared/ に抽出**
3. **型定義は model/ や types.ts に集約**
4. **`import type` を活用してランタイム依存を減らす**

---

**次のステップ**: `npm run dep:circular` を実行してみましょう！
