# 将軍データセット取得モジュール

将軍システムの6種類のデータセット（flash/final × receive/shipment/yard）をDBから取得するための機能を提供します。

## 概要

- **目的:** 将軍CSV（shogun_flash/final × receive/shipment/yard）をDBから統一的に取得
- **設計:** Clean Architecture、SOLID原則に準拠
- **依存性注入:** SQLAlchemy Session を外部から注入

## 主要コンポーネント

### 1. ShogunDatasetKey（dataset_keys.py）

6種類のデータセットキーをEnumで定義し、typoを防止します。

```python
from backend_shared.shogun import ShogunDatasetKey

# 使用可能なキー
ShogunDatasetKey.SHOGUN_FINAL_RECEIVE    # 受入一覧（確定）
ShogunDatasetKey.SHOGUN_FINAL_SHIPMENT   # 出荷一覧（確定）
ShogunDatasetKey.SHOGUN_FINAL_YARD       # ヤード一覧（確定）
ShogunDatasetKey.SHOGUN_FLASH_RECEIVE    # 受入一覧（速報）
ShogunDatasetKey.SHOGUN_FLASH_SHIPMENT   # 出荷一覧（速報）
ShogunDatasetKey.SHOGUN_FLASH_YARD       # ヤード一覧（速報）

# プロパティ
key.is_final        # => True/False
key.is_flash        # => True/False
key.data_type       # => "receive"/"shipment"/"yard"
key.get_view_name() # => "v_active_shogun_final_receive"
key.get_master_key()# => "receive"
```

### 2. ShogunMasterNameMapper（master_name_mapper.py）

master.yaml（shogun_csv_masters.yaml）を使って、DB英語名⇔日本語名の変換を行います。

```python
from backend_shared.shogun import ShogunMasterNameMapper

mapper = ShogunMasterNameMapper()

# データセット名の日本語表示
label = mapper.get_dataset_label("shogun_final_receive")
# => "受入一覧"

# カラム名変換（英→日）
ja_name = mapper.get_ja_column_name("receive", "slip_date")
# => "伝票日付"

# カラム名変換（日→英）
en_name = mapper.get_en_column_name("receive", "伝票日付")
# => "slip_date"

# 全カラム定義取得
columns = mapper.get_all_columns("receive")
# => {日本語名: {en_name: ..., type: ...}, ...}

# マッピング辞書取得
en_to_ja = mapper.get_en_to_ja_map("receive")
# => {"slip_date": "伝票日付", ...}
```

### 3. ShogunDatasetFetcher（fetcher.py）

DBから将軍データセットを取得するメインクラスです。

```python
from sqlalchemy.orm import Session
from backend_shared.shogun import ShogunDatasetFetcher, ShogunDatasetKey
from datetime import date

# Session は外部から注入
fetcher = ShogunDatasetFetcher(db_session)

# 基本的な取得（list[dict]形式）
data = fetcher.fetch(ShogunDatasetKey.SHOGUN_FINAL_RECEIVE)

# 日付範囲指定
data = fetcher.fetch(
    ShogunDatasetKey.SHOGUN_FINAL_RECEIVE,
    start_date=date(2024, 4, 1),
    end_date=date(2024, 10, 31),
    limit=10000
)

# DataFrame形式で取得
df = fetcher.fetch_df(ShogunDatasetKey.SHOGUN_FLASH_SHIPMENT)

# 便利メソッド（6種類）
data = fetcher.get_final_receive(start_date=date(2024, 4, 1))
data = fetcher.get_final_shipment(limit=1000)
data = fetcher.get_final_yard()
data = fetcher.get_flash_receive()
data = fetcher.get_flash_shipment()
data = fetcher.get_flash_yard()

# データセットラベル取得
label = fetcher.get_dataset_label(ShogunDatasetKey.SHOGUN_FINAL_RECEIVE)
# => "受入一覧"
```

## 使用例

### 例1: 受入実績データの取得

```python
from sqlalchemy.orm import Session
from backend_shared.shogun import ShogunDatasetFetcher, ShogunDatasetKey
from datetime import date

def fetch_historical_inbound_data(db: Session, days: int = 30) -> list[dict]:
    """
    過去N日分の受入実績データを取得
    """
    fetcher = ShogunDatasetFetcher(db)
    
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    data = fetcher.fetch(
        ShogunDatasetKey.SHOGUN_FINAL_RECEIVE,
        start_date=start_date,
        end_date=end_date
    )
    
    return data
```

### 例2: 複数データセットの取得

```python
def fetch_all_shogun_data(db: Session, target_date: date) -> dict:
    """
    指定日の全将軍データを取得
    """
    fetcher = ShogunDatasetFetcher(db)
    
    return {
        "receive": fetcher.get_final_receive(
            start_date=target_date,
            end_date=target_date
        ),
        "shipment": fetcher.get_final_shipment(
            start_date=target_date,
            end_date=target_date
        ),
        "yard": fetcher.get_final_yard(
            start_date=target_date,
            end_date=target_date
        ),
    }
```

### 例3: DataFrame形式で分析

```python
import pandas as pd

def analyze_receive_data(db: Session) -> pd.DataFrame:
    """
    受入データを集計分析
    """
    fetcher = ShogunDatasetFetcher(db)
    
    # DataFrameで取得
    df = fetcher.fetch_df(
        ShogunDatasetKey.SHOGUN_FINAL_RECEIVE,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31)
    )
    
    # 集計処理
    summary = df.groupby("vendor_cd").agg({
        "net_weight": "sum",
        "quantity": "sum",
        "amount": "sum"
    })
    
    return summary
```

## テスト

### ユニットテスト（DB不要）

```bash
# ShogunDatasetKey のテスト
pytest tests/test_shogun_fetcher.py::TestShogunDatasetKey -v

# ShogunMasterNameMapper のテスト（一部）
pytest tests/test_shogun_fetcher.py::TestShogunMasterNameMapper::test_extract_master_key -v
```

### 統合テスト（DB必要）

実際のDBに接続してテストする場合は、`@pytest.mark.skipif` を外して実行してください。

```bash
# 統合テスト実行（DB接続必要）
pytest tests/test_shogun_fetcher.py -v -m "not skipif"
```

## アーキテクチャ

```
backend_shared/shogun/
├── __init__.py              # 公開API
├── dataset_keys.py          # データセットキー定義（Enum）
├── master_name_mapper.py    # master.yaml 名前変換
└── fetcher.py               # データ取得クラス（メイン）

依存関係:
- backend_shared.config.config_loader (ShogunCsvConfigLoader)
- backend_shared.config.paths (SHOGUNCSV_DEF_PATH)
- backend_shared.db.names (view名定数)
- backend_shared.application.logging (ログ)
- sqlalchemy.orm.Session (外部注入)
```

## 設計原則

### Clean Architecture
- **Domain層:** ShogunDatasetKey（ドメイン知識）
- **Port:** Session注入（I/O境界）
- **Adapter:** ShogunDatasetFetcher（具体実装）

### SOLID原則
- **単一責任:** 各クラスが明確な責務を持つ
- **依存性注入:** Session を外部から注入
- **インターフェース分離:** 必要な機能のみ公開
- **開放閉鎖:** 新しいデータセット追加が容易

### 既存構造との整合性
- `ShogunCsvConfigLoader` を活用
- `backend_shared.db.names` のview名定数を使用
- `backend_shared.application.logging` で統一ログ
- 既存の命名規則・コーディングスタイルに準拠

## エラーハンドリング

```python
from backend_shared.shogun import ShogunDatasetFetcherError

try:
    data = fetcher.fetch("invalid_key")
except ShogunDatasetFetcherError as e:
    # エラーメッセージに原因が含まれる
    print(f"データ取得失敗: {e}")
```

エラーの種類:
- **不正なdataset_key:** 有効な値のリストを含むエラーメッセージ
- **view未定義:** dataset_keyに対応するview名が未定義
- **DB接続エラー:** SQLAlchemyの例外をラップして再送出

## パフォーマンス

- `lru_cache` でmaster.yamlを1プロセス1回のみ読み込み
- `limit` パラメータで取得件数を制限可能
- インデックス活用: `slip_date` でフィルタ・ソート

## 今後の拡張

### 可能な拡張ポイント
1. 非同期版（AsyncSession対応）
2. キャッシュ機構（Redis等）
3. ページネーション対応
4. 追加フィルタ（業者CD、品名CD等）
5. 集計機能（groupby、sum等）

### 追加データセット
新しいデータセットは `ShogunDatasetKey` に追加するだけで対応可能:

```python
class ShogunDatasetKey(str, Enum):
    # 既存6種類...
    
    # 新規追加（例）
    SHOGUN_FINAL_PAYMENT = "shogun_final_payment"
    
    def get_view_name(self) -> str:
        if self == ShogunDatasetKey.SHOGUN_FINAL_PAYMENT:
            return "v_active_shogun_final_payment"
        return f"v_active_{self.value}"
```

## まとめ

✅ **完了:**
- 6種類のデータセット取得機能
- master.yaml による名前変換
- Clean Architecture / SOLID 準拠
- ユニットテスト実装
- 既存構造を壊さない追加

🔍 **検証済み:**
- view名: `backend_shared.db.names` から確認
- master.yaml パス: `/backend/config/csv_config/shogun_csv_masters.yaml`
- DBアクセス: SQLAlchemy Session 注入パターン

📦 **公開API:**
- `backend_shared.shogun.ShogunDatasetKey`
- `backend_shared.shogun.ShogunDatasetFetcher`
- `backend_shared.shogun.ShogunMasterNameMapper`
