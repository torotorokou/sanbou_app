# コードスタイルガイド

## 概要

本プロジェクトでは、**競合しない静的解析・整形基盤**を採用しています：

### Python
- **black**: コードフォーマッター（唯一の整形ツール）
- **ruff**: Linter + Import整形（isortの代替）

### Frontend (React+TypeScript)
- **prettier**: コードフォーマッター（唯一の整形ツール）
- **eslint**: Linter（prettier競合回避設定済み）

## ツール責務

| ツール | 役割 | 競合回避策 |
|--------|------|-----------|
| **black** | Python整形 | ruffでE203/E501/W503を無視 |
| **ruff** | Pythonリント + import整形 | black互換設定、isort不使用 |
| **prettier** | Frontend整形 | eslint-config-prettierで競合回避 |
| **eslint** | Frontendリント | prettierルールを無効化 |

## ディレクトリ構成

```
/home/koujiro/work_env/22.Work_React/sanbou_app/
├── pyproject.toml              # Python設定の正本（black + ruff）
├── .pre-commit-config.yaml     # pre-commit hooks設定
└── app/frontend/
    ├── .prettierrc.json        # prettier設定
    ├── .prettierignore         # prettier除外
    ├── eslint.config.js        # eslint設定（prettier競合回避）
    └── package.json            # npm scripts
```

## コマンド一覧

### Python

```bash
# フォーマット（整形のみ）
black app/backend

# リント + Import整形（自動修正）
ruff check --fix app/backend

# リントのみ（修正なし）
ruff check app/backend

# pre-commit経由で実行
pre-commit run black --all-files
pre-commit run ruff --all-files
```

### Frontend

```bash
cd app/frontend

# フォーマット（整形のみ）
npm run format
# または
prettier --write "src/**/*.{ts,tsx,js,jsx,json,css}"

# リント（自動修正）
npm run lint:fix
# または
eslint "src/**/*.{ts,tsx}" --fix

# 確認のみ
npm run format:check  # prettier
npm run lint          # eslint
```

### 全体

```bash
# pre-commit全実行（Python + Frontend）
pre-commit run --all-files

# 個別hook実行
pre-commit run black --all-files
pre-commit run ruff --all-files
pre-commit run prettier --all-files
pre-commit run eslint --all-files
```

## 設定ファイル詳細

### Python設定 ([pyproject.toml](../../pyproject.toml))

```toml
[tool.black]
line-length = 100
target-version = ['py310']

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP"]
ignore = [
    "E203",  # Whitespace before ':' (black互換)
    "E501",  # Line too long (blackに任せる)
    "W503",  # Line break before binary operator (blackスタイル)
]

[tool.ruff.lint.isort]
known-first-party = ["app", "backend_shared"]
lines-after-imports = 2
```

### Frontend設定

#### [.prettierrc.json](../../app/frontend/.prettierrc.json)

```json
{
  "printWidth": 100,
  "tabWidth": 2,
  "semi": true,
  "singleQuote": true,
  "trailingComma": "es5"
}
```

#### [eslint.config.js](../../app/frontend/eslint.config.js)

```javascript
import eslintConfigPrettier from "eslint-config-prettier";

export default defineConfig([
  // ... 他のルール ...
  
  // 最後にprettier競合回避（必須）
  eslintConfigPrettier,
]);
```

## トラブルシューティング

### 問題: blackとruffがループする

**原因**: isortが別途動作している  
**解決**: isortを削除し、ruffのI系ルールのみ使用

### 問題: prettierとeslintが競合する

**原因**: eslintに整形ルール（quotes, semi等）が含まれている  
**解決**: `eslint-config-prettier`を最後に配置

### 問題: pre-commitが遅い

**原因**: 全ファイルをチェックしている  
**解決**: Staged filesのみチェック（デフォルト動作）

```bash
# 全ファイル実行は手動で
pre-commit run --all-files
```

## VSCode設定推奨

```json
{
  "editor.formatOnSave": true,
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.codeActionsOnSave": {
      "source.organizeImports": "explicit"  // ruff
    }
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

## CI/CD統合

```yaml
# GitHub Actions例
- name: Run pre-commit
  run: |
    pre-commit run --all-files --show-diff-on-failure
```

## 参考

- [Black](https://black.readthedocs.io/)
- [Ruff](https://docs.astral.sh/ruff/)
- [Prettier](https://prettier.io/)
- [ESLint](https://eslint.org/)
- [pre-commit](https://pre-commit.com/)
