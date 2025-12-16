# Alembic 運用ルール（暫定）

本ドキュメントは、本プロジェクトにおける **Alembic マイグレーションの運用ルール**を整理したものです。  
「誰がやっても同じ品質・同じ手順で進む」ことを目的にします。

---

## 1. 基本方針

- **小さく作る（ベイビーステップ）**
  - 1マイグレーション = 1テーマ（例：テーブル1枚追加、ビュー1本追加）
  - 無関係な変更を同じrevisionに混ぜない
- **必ず downgrade を用意する**
  - 本番でのロールバックを想定し、upgrade/downgrade が対になるようにする
- **破壊的変更は避ける / 段階的に**
  - DROP / RENAME / 型変更は影響が大きい。必要なら段階的（追加→移行→切替→削除）にする
- **routersやアプリのロジックにSQLを埋めない**
  - DB構造変更は Alembic で管理し、SQLは原則マイグレーション（またはSQLファイル）に集約する

---

## 2. ファイル命名ルール（versions配下）

### 2.1 ファイル名は「日付＋連番」
- 形式：`YYYYMMDD_NNN_<slug>.py`
  - `YYYYMMDD`：作成日（JST基準）
  - `NNN`：その日内の連番（001, 002, 003...）
  - `<slug>`：内容が分かる短い英語（例：`add_reserve_tables`）

例：
- `20251216_001_add_reserve_daily_manual.py`
- `20251216_002_add_reserve_customer_daily.py`
- `20251216_003_add_v_reserve_daily_for_forecast.py`

### 2.2 revision id（`revision = "..."`）は「何でも可」
- **ファイル名と一致していなくてよい**（ただし、ユニークであること）
- 推奨：Alembicが生成したIDをそのまま使う（衝突しづらい）
- 重要：**ファイル名を変更しても `revision` / `down_revision` が正しければ動く**

---

## 3. 作業手順（推奨フロー）

### Step 1) 新しいrevisionを作る
```bash
alembic revision -m "add_reserve_daily_manual"
```

### Step 2) versions配下の生成ファイルを「日付＋連番」にリネームする
- 例（生成物が `a1b2c3d4_add_reserve_daily_manual.py` だった場合）
  - `20251216_001_add_reserve_daily_manual.py` にリネームする
- 注意：
  - ファイルの中身（`revision = "a1b2c3d4"` など）は **基本そのまま**
  - `down_revision` は手順どおりにチェーンさせる

### Step 3) upgrade / downgrade を実装する
- CREATE TABLE / CREATE VIEW などを upgrade に
- DROP TABLE / DROP VIEW などを downgrade に
- 可能なら安全策（IF EXISTS / OR REPLACE 等）を検討（プロジェクト方針に合わせる）

### Step 4) ローカルで検証する
```bash
alembic upgrade head
alembic downgrade -1
alembic upgrade head
```

### Step 5) コミット
- **Phase単位（小さく）**でコミットする
- コミットメッセージ例：
  - `db: add reserve_daily_manual (alembic)`
  - `db: add reserve_customer_daily (alembic)`
  - `db: add v_reserve_daily_for_forecast (alembic)`

---

## 4. 連番（NNN）の運用ルール

- 同日内で新規ファイルを作るたびに `NNN` を +1 する
- 連番の採番基準：
  - リポジトリ内 `migrations/versions/` を見て、その日の最大NNN+1
- 迷ったら：
  - 既存ファイルと重複しない番号を選ぶ（001〜999）

---

## 5. SQLを分離する場合（推奨）

長いSQL（ビュー定義、マテビュー、複雑な更新など）は、可読性のため **SQLファイルに分離**してよい。

推奨構成例：
- `migrations/sql/20251216_003_add_v_reserve_daily_for_forecast.sql`

マイグレーションから読み込む（例）：
- `op.execute(Path(sql_path).read_text(encoding="utf-8"))`

ルール：
- SQLファイル名も **日付＋連番**で揃える
- マイグレーションは「SQLを実行する責務」に絞る（可読性を上げる）

---

## 6. チェックリスト（最低限）

- [ ] ファイル名が `YYYYMMDD_NNN_*.py` になっている
- [ ] `revision` と `down_revision` が正しい（依存順）
- [ ] upgrade / downgrade が対になっている
- [ ] ローカルで `upgrade head` / `downgrade -1` が通る
- [ ] 破壊的変更の影響範囲を説明できる（必要なら段階移行）
- [ ] 1revision 1テーマになっている

---

## 7. よくある落とし穴

- **ファイル名を変えたら動かない**  
  → 動きます。Alembicはファイル名ではなく `revision`/`down_revision` を読みます（ただし読み込み対象ディレクトリにあること）。
- **downgrade を書かない**  
  → 後で詰みます。最初から必ず書く。
- **大きすぎるマイグレーション**  
  → レビュー不能になるので、テーマを分割する。

---

## 8. 例：予約テーブル追加（想定）

- `20251216_001_add_reserve_daily_manual.py`  
- `20251216_002_add_reserve_customer_daily.py`  
- `20251216_003_add_v_reserve_daily_for_forecast.py`

この3本に分けて作る（おすすめ）。

---

更新履歴：
- 2025-12-16 初版作成
