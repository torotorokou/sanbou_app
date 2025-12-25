# 型チェック（mypy）の段階的導入

## 📖 概要

このプロジェクトでは **mypy** を使った静的型チェックを **段階的に導入** しています。

### なぜ段階導入か？

- **既存コードが大きい**：一度に全体を型付けすると開発が止まる
- **学習コスト**：チーム全体が型ヒントに慣れる時間が必要
- **ツール競合回避**：mypy/ruff/black の役割分担を明確にする

### 役割分担

| ツール | 役割 | 実行タイミング |
|--------|------|--------------|
| **black** | コードフォーマッター（唯一の真実） | pre-commit, make fmt-python |
| **ruff** | Linter（import整形、コードチェック） | pre-commit, make fmt-python |
| **mypy** | 型チェッカー（型の整合性） | 手動 or CI（軽く） |

**重要**：
- black が formatter の責任を持つ
- ruff-format は使わない（競合を避けるため）
- mypy はフォーマットに関与しない（型のみ）

---

## 🎯 現在の対象範囲

段階導入のため、最初は **core層とapi層のみ** を対象としています。

### Phase 1（現在）：core + api
- ✅ `app/backend/core_api/app/core/` - ドメイン、ユースケース
- ✅ `app/backend/core_api/app/api/` - ルーター、エンドポイント

### Phase 2（将来）：infra層を追加
- ⏳ `app/backend/core_api/app/infra/` - データベース、外部API

### Phase 3（最終）：全体
- ⏳ config/, scheduler/, shared/ などすべて

---

## 🚀 使い方

### ローカルで型チェック

```bash
# core層のみチェック（推奨）
make typecheck

# または個別に
make typecheck-core  # core層のみ
make typecheck-api   # api層のみ

# 全体チェック（将来用、現時点では多くのエラーが出る）
make typecheck-all
```

### Docker なしで実行（開発用）

```bash
cd app/backend/core_api
mypy app/core --config-file=pyproject.toml
```

---

## ⚙️ 設定方針（ゆるく開始）

`app/backend/core_api/pyproject.toml` の `[tool.mypy]` セクション参照。

### 現在の設定（Phase 1）

```toml
[tool.mypy]
python_version = "3.11"
strict = false  # 段階導入のため無効

# 基本的な警告
warn_return_any = true
warn_unused_configs = true
warn_unused_ignores = true
warn_redundant_casts = true
no_implicit_optional = true

# 外部ライブラリで詰まらない
ignore_missing_imports = true

# 最初は緩く
check_untyped_defs = false
disallow_untyped_defs = false
disallow_untyped_calls = false
```

### 将来的に厳格化（Phase 2-3）

```toml
# Phase 2 で追加予定
check_untyped_defs = true

# Phase 3 で追加予定
disallow_untyped_defs = true
disallow_untyped_calls = true
strict = true
```

---

## 🔧 よくあるエラーと対処

### 1. `error: Cannot find implementation or library stub for module named 'xxx'`

**原因**：外部ライブラリの型スタブがない

**対処**：
```bash
# 型スタブをインストール（例：requests）
pip install types-requests

# または mypy で無視
# pyproject.toml の [tool.mypy] に追加
[[tool.mypy.overrides]]
module = "xxx.*"
ignore_missing_imports = true
```

### 2. `error: Function is missing a return type annotation`

**原因**：関数の戻り値の型が未指定

**対処**：
```python
# Before
def get_user(id: int):
    return User.query.get(id)

# After
def get_user(id: int) -> User | None:
    return User.query.get(id)
```

### 3. `error: Argument 1 has incompatible type "str"; expected "int"`

**原因**：引数の型が不一致

**対処**：
```python
# Before
def process(value: int) -> None:
    ...

process("123")  # エラー

# After
process(int("123"))  # OK
```

### 4. `error: Incompatible return value type (got "None", expected "User")`

**原因**：関数が None を返す可能性があるのに型に含まれていない

**対処**：
```python
# Before
def get_user(id: int) -> User:
    return User.query.get(id)  # None の可能性

# After
def get_user(id: int) -> User | None:
    return User.query.get(id)
```

---

## 📚 ロードマップ

### Phase 1（現在）：基盤整備
- [x] mypy 設定をゆるく調整
- [x] Makefile に `make typecheck` 追加
- [x] ドキュメント作成
- [x] core層 + api層 のみ対象

### Phase 2（次のステップ）：型注釈の追加
- [ ] core層の主要クラスに型注釈を追加
  - [ ] ドメインモデル
  - [ ] ユースケース
  - [ ] リポジトリインターフェース
- [ ] api層のエンドポイントに型注釈を追加
- [ ] `check_untyped_defs = true` に変更

### Phase 3（将来）：範囲拡大
- [ ] infra層を型チェック対象に追加
- [ ] config/, scheduler/ も対象に
- [ ] `disallow_untyped_defs = true` に変更
- [ ] CI で型チェックを必須化（軽く）

### Phase 4（最終）：厳格化
- [ ] `strict = true` に変更
- [ ] 全コードが型チェックを通過
- [ ] pre-commit に mypy を追加（段階的ファイルのみ）

---

## 🚫 やってはいけないこと

### ❌ 初回から strict = true にする
開発が止まり、モチベーションが下がる。段階的に厳格化する。

### ❌ pre-commit で全ファイルを mypy チェック
WSL環境でCPU負荷が高く、VSCodeが切断される。対象を限定すること。

### ❌ ruff-format を使う
black と競合する。formatter は black のみ。

### ❌ 型エラーを `# type: ignore` で全部消す
型チェックの意味がなくなる。本当に必要な箇所だけ使用。

---

## 💡 ベストプラクティス

### ✅ 新規コードは型注釈を付ける
```python
# Good
def create_user(name: str, age: int) -> User:
    return User(name=name, age=age)
```

### ✅ 既存コードは段階的に型付け
- まず関数のシグネチャ（引数・戻り値）から
- 次に変数の型ヒント
- 最後に複雑な型（Generic, Protocol 等）

### ✅ 型エラーは早めに修正
- 後回しにすると積み重なる
- 1ファイルずつ型チェックを通す

### ✅ CI は軽く
- 対象ディレクトリを限定
- `|| true` で失敗しても続行（Phase 1-2）
- Phase 3 以降で厳格化

---

## 🔗 参考リンク

- [mypy 公式ドキュメント](https://mypy.readthedocs.io/)
- [Python 型ヒント（PEP 484）](https://peps.python.org/pep-0484/)
- [typing モジュール](https://docs.python.org/3/library/typing.html)
- [型チェッカー比較（mypy vs pyright）](https://github.com/microsoft/pyright#comparing-pyright-and-mypy)

---

## ❓ FAQ

### Q: pyright と mypy の違いは？

**A**: pyright は高速だが、mypy の方が柔軟性が高く段階導入に向いている。現時点では mypy を採用。

### Q: 型チェックはいつ実行する？

**A**: 
- ローカル：コミット前に `make typecheck`（任意）
- CI：PR時に自動実行（Phase 2 以降）
- pre-commit：対象を限定して追加予定（Phase 3 以降）

### Q: 型エラーが大量に出る場合は？

**A**: 
1. 対象ディレクトリをさらに限定（`typecheck-core` のみ）
2. 特定のモジュールを除外（`pyproject.toml` の `exclude` に追加）
3. 段階的に修正（1ファイルずつ）

### Q: `# type: ignore` はいつ使う？

**A**: 
- 外部ライブラリの型スタブがない場合
- 動的な型変換が避けられない場合
- 一時的な回避（後で修正予定）

**使いすぎ注意**：型チェックの意味がなくなる。

---

## 📝 更新履歴

- 2025-12-25: 初版作成（Phase 1 完了）
