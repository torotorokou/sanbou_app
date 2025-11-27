# Report Feature リファクタリング計画

## 問題点
1. hooks/とmodel/に同じファイルが重複
2. FSDアーキテクチャ違反（hooks層は不要）
3. インポートパスの混乱

## 実施内容

### 1. 重複ファイル削除
- hooks/ ディレクトリを完全削除
- model/ のファイルを正として使用

### 2. インポートパス更新
- `../hooks/*` → `../model/*`
- `../../hooks/*` → `../../model/*`

### 3. features/report/index.ts 更新
- hooks/ からのエクスポートをmodel/に変更

### 4. 最終構成
```
features/report/
├── api/          # APIコール専用
├── config/       # 設定ファイル
├── model/        # ビジネスロジック・フック
│   └── config/   # レポート設定
└── ui/           # UIコンポーネント
```
