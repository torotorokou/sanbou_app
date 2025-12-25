"""
Shogun CSV Repository

将軍CSVデータをDBに保存するリポジトリ。
backend_sharedのCSVバリデーター・フォーマッターを活用します。
YAMLファイル(shogun_csv_masters.yaml)から動的にカラムマッピングを取得します。
"""

import pandas as pd
import sqlalchemy as sa
from app.config.settings import get_settings
from app.infra.db.dynamic_models import (
    create_shogun_model_class,
    get_shogun_model_class,
)
from app.infra.db.table_definition import get_table_definition_generator
from backend_shared.application.logging import create_log_context, get_module_logger
from backend_shared.infra.dataframe import filter_defined_columns, to_sql_ready_df
from backend_shared.infra.json_utils import deep_jsonable
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = get_module_logger(__name__)


class ShogunCsvRepository:
    """将軍CSV保存リポジトリ（YAMLベース）"""

    def __init__(
        self,
        db: Session,
        table_map: dict[str, str] | None = None,
        schema: str | None = None,
    ):
        """
        Args:
            db: SQLAlchemy Session
            table_map: テーブル名マッピング（オプション）
                例: {"receive": "receive_flash", "yard": "yard_flash", "shipment": "shipment_flash"}
            schema: スキーマ名（オプション、デフォルトは search_path に従う）
        """
        self.db = db
        self.settings = get_settings()
        self.table_gen = get_table_definition_generator()
        self._table_map = table_map or {}  # テーブル名上書き用
        self._schema = schema  # 将来的にORM側でも利用可能

    def save_csv_by_type(self, csv_type: str, df: pd.DataFrame) -> int:
        """
        CSV種別に応じて適切なテーブルに保存

        処理フロー:
          1. テーブル名決定（table_map での上書き or デフォルト shogun_flash_*）
          2. YAMLから日本語→英語のカラムマッピングを取得
          3. DataFrameのカラム名を日本語→英語に変換
          4. raw層 vs stg層で異なる処理:
             - raw層: 全カラムを TEXT 型で保存（生データの完全性を保持）
             - stg層: YAML定義カラムのみを抽出（正規化済みデータ）
          5. pandas.DataFrame.to_sql() でバルクインサート

        設計方針:
          - YAML駆動: テーブル定義やカラムマッピングはYAMLで管理（コード変更不要）
          - 二層アーキテクチャ:
            * raw層: 完全な生データ（監査・トラブルシューティング用）
            * stg層: 正規化済みデータ（分析・集計用）
          - トラッキングカラム: upload_file_id, source_row_no で元ファイルとの紐付け

        Args:
            csv_type: CSV種別 ('receive', 'yard', 'shipment')
            df: 保存するDataFrame
                - raw層: 日本語カラム名（元のCSVそのまま）→ 英語に変換のみ、全カラム保持
                - stg層: 日本語カラム名（元のCSV）→ 英語に変換+YAML定義カラムのみ抽出

        Returns:
            int: 保存した行数

        Raises:
            Exception: DB保存に失敗した場合
        """
        if df.empty:
            logger.warning(
                "DataFrameが空のため保存スキップ",
                extra=create_log_context(
                    operation="save_dataframe_to_stg", csv_type=csv_type
                ),
            )
            return 0

        # スキーマとテーブル名の決定
        schema = self._schema or "stg"

        # テーブル名の上書きチェック
        override_table = self._table_map.get(csv_type)
        if override_table:
            # table_map が指定された場合: カスタムテーブル名を使用
            table_name = override_table
        else:
            # table_map が未指定の場合: デフォルトは shogun_flash_*
            # raw.shogun_flash_receive, stg.shogun_flash_receive など
            table_name = f"shogun_flash_{csv_type}"

        # YAMLから日本語→英語のカラムマッピングを取得
        column_mapping = self.table_gen.get_column_mapping(csv_type)

        # DataFrame のカラム名を日本語→英語に変換
        df_renamed = df.rename(columns=column_mapping)
        logger.info(
            f"[DEBUG REPO] {schema}.{csv_type}: After rename, columns={list(df_renamed.columns)[:15]}"
        )
        logger.info(
            f"[DEBUG REPO] Has upload_file_id={('upload_file_id' in df_renamed.columns)}, Has source_row_no={('source_row_no' in df_renamed.columns)}"
        )

        # raw層とstg層で異なる処理
        if schema == "raw":
            # raw層: 全カラムを保持（YAML定義外のカラムも含む）
            # TEXT型として保存（生データの完全性を保持）
            df_to_save = df_renamed.astype(str)  # 全カラムを文字列化
            df_to_save = df_to_save.replace(
                ["nan", "NaT", "<NA>"], ""
            )  # pandas特有の文字列を空文字列に変換
            logger.info(
                f"[DEBUG REPO] [raw] Saving {csv_type} with ALL columns ({len(df_to_save.columns)} cols): {list(df_to_save.columns)[:10]}"
            )
        else:
            # stg層: YAMLで定義されたカラムのみを抽出
            columns_def = self.table_gen.get_columns_definition(csv_type)
            valid_columns = [col["en_name"] for col in columns_def]
            logger.info(
                f"[DEBUG REPO] [stg] YAML valid columns for {csv_type}: {len(valid_columns)} cols"
            )

            # upload_file_id と source_row_no は保持（トラッキング用カラム）
            tracking_columns = []
            if "upload_file_id" in df_renamed.columns:
                tracking_columns.append("upload_file_id")
                logger.info("[DEBUG REPO] [stg] Found upload_file_id in df_renamed")
            if "source_row_no" in df_renamed.columns:
                tracking_columns.append("source_row_no")
                logger.info("[DEBUG REPO] [stg] Found source_row_no in df_renamed")

            # YAML定義カラム + トラッキングカラムを保持
            valid_columns_with_tracking = valid_columns + tracking_columns
            logger.info(
                f"[DEBUG REPO] [stg] Before filter: {len(df_renamed.columns)} cols, After filter will keep: {len(valid_columns_with_tracking)} cols"
            )
            df_to_save = filter_defined_columns(
                df_renamed, valid_columns_with_tracking, log_dropped=True
            )
            logger.info(
                f"[DEBUG REPO] [stg] After filter: {len(df_to_save.columns)} cols: {list(df_to_save.columns)[:15]}"
            )

            # SQL 保存可能な型に正規化（pandas特有の型をPython標準型に変換）
            df_to_save = to_sql_ready_df(df_to_save)
            logger.info(
                f"[DEBUG REPO] [stg] After to_sql_ready: {len(df_to_save.columns)} cols: {list(df_to_save.columns)[:15]}"
            )

        model_class = create_shogun_model_class(
            csv_type, table_name=table_name, schema=schema
        )

        # [DEBUG] モデルクラスのカラム定義を確認
        model_columns = [c.name for c in model_class.__table__.columns]
        logger.info(
            f"[DEBUG REPO] [{schema}] Model has {len(model_columns)} columns: {model_columns[:15]}"
        )

        # DataFrameを辞書のリストに変換
        records = df_to_save.to_dict("records")
        logger.info(f"[DEBUG REPO] Preparing bulk insert: {len(records)} records")
        if records:
            logger.info(
                f"[DEBUG REPO] First record keys: {list(records[0].keys())[:15]}"
            )
            logger.info(f"[DEBUG REPO] First record sample: {records[0]}")

        # Pandas特有の型をJSON互換型に変換（np.int64 → int, np.float64 → float等）
        payloads = []
        for idx, record in enumerate(records):
            payload = deep_jsonable(record)

            # id カラムは自動採番されるため、payload から除外
            payload.pop("id", None)

            if idx == 0:
                logger.info(
                    f"[DEBUG REPO] First payload keys ({len(payload)} keys): {list(payload.keys())[:15]}"
                )
                logger.info(f"[DEBUG REPO] First payload sample: {payload}")
                # [DEBUG] モデルに存在しないキーをチェック
                payload_keys = set(payload.keys())
                model_keys = set(model_columns) - {
                    "id",
                    "created_at",
                }  # id, created_at は自動生成
                missing_in_model = payload_keys - model_keys
                missing_in_payload = model_keys - payload_keys
                if missing_in_model:
                    logger.warning(
                        f"[DEBUG REPO] Payload has keys not in model: {missing_in_model}"
                    )
                if missing_in_payload:
                    logger.warning(
                        f"[DEBUG REPO] Model has columns not in payload: {missing_in_payload}"
                    )

            payloads.append(payload)

        try:
            # pandas.DataFrame.to_sql() を使用してバルクインサート
            # bulk_insert_mappings は None 値を含むカラムをスキップする問題があるため使用しない
            df_final = pd.DataFrame(payloads)

            # created_at は DB 側で自動生成されるため除外
            if "created_at" in df_final.columns:
                df_final = df_final.drop(columns=["created_at"])

            # 空行をフィルタリング (slip_date が None または NaN の行を除外)
            if "slip_date" in df_final.columns:
                before_len = len(df_final)
                df_final = df_final[df_final["slip_date"].notna()]
                after_len = len(df_final)
                if before_len != after_len:
                    logger.info(
                        f"[DEBUG REPO] Filtered out {before_len - after_len} empty rows (slip_date=None)"
                    )

            logger.info(
                f"[DEBUG REPO] Final DataFrame columns before to_sql: {list(df_final.columns)[:15]}"
            )
            logger.info(f"[DEBUG REPO] Final DataFrame shape: {df_final.shape}")

            # raw層では全カラムをVARCHAR/TEXTで保存する(ただしINTEGER型カラムは除く)
            dtype_spec = None
            if schema == "raw":
                # raw層は全て文字列型で保存(INTEGER型カラムを除く)
                dtype_spec = {}
                integer_columns = {"source_row_no", "upload_file_id"}
                for col in df_final.columns:
                    if col in integer_columns:
                        dtype_spec[col] = sa.INTEGER
                    else:
                        dtype_spec[col] = sa.TEXT
                logger.info(
                    f"[DEBUG REPO] Using TEXT dtype for raw layer (except INTEGER columns: {integer_columns})"
                )

            # to_sql() でバルクインサート
            df_final.to_sql(
                name=table_name,
                con=self.db.bind,
                schema=schema,
                if_exists="append",
                index=False,
                method="multi",
                chunksize=1000,
                dtype=dtype_spec,
            )
            # NOTE: commit()はUseCaseレイヤーで実行（トランザクション境界の統一）

            logger.info(
                "CSVデータ保存完了",
                extra=create_log_context(
                    operation="save_dataframe_to_stg",
                    rows_count=len(payloads),
                    schema=schema,
                    table_name=table_name,
                    csv_type=csv_type,
                ),
            )
            return len(payloads)

        except Exception as e:
            # NOTE: rollback()もUseCaseレイヤーで実行（例外は再raiseのみ）
            logger.error(
                "CSVデータ保存失敗",
                extra=create_log_context(
                    operation="save_dataframe_to_stg",
                    csv_type=csv_type,
                    schema=schema,
                    table_name=table_name,
                    error=str(e),
                ),
                exc_info=True,
            )
            raise

    def save_receive_csv(self, df: pd.DataFrame) -> int:
        """受入一覧CSVを保存"""
        return self.save_csv_by_type("receive", df)

    def save_yard_csv(self, df: pd.DataFrame) -> int:
        """ヤード一覧CSVを保存"""
        return self.save_csv_by_type("yard", df)

    def save_shipment_csv(self, df: pd.DataFrame) -> int:
        """出荷一覧CSVを保存"""
        return self.save_csv_by_type("shipment", df)

    def truncate_table(self, csv_type: str) -> None:
        """
        指定したCSV種別のテーブルを全削除（開発・テスト用）

        Args:
            csv_type: CSV種別 ('receive', 'yard', 'shipment')
        """
        table_name = self.settings.get_table_name(csv_type)
        if not table_name:
            raise ValueError(f"Unknown csv_type: {csv_type}")

        try:
            # TRUNCATE実行
            self.db.execute(
                text(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE")
            )
            # NOTE: commit()はUseCase/API層で実行（テスト用途なのでここではコミット）
            # 開発・テスト用のため、この関数だけは例外的にcommit()を残す
            self.db.commit()
            logger.info(
                "テーブルtruncate完了",
                extra=create_log_context(
                    operation="truncate_table", table_name=table_name
                ),
            )
        except Exception as e:
            self.db.rollback()
            logger.error(
                "テーブルtruncate失敗",
                extra=create_log_context(
                    operation="truncate_table", table_name=table_name, error=str(e)
                ),
                exc_info=True,
            )
            raise

    def get_record_count(self, csv_type: str) -> int:
        """
        指定したCSV種別のテーブルのレコード数を取得

        Args:
            csv_type: CSV種別 ('receive', 'yard', 'shipment')

        Returns:
            int: レコード数
        """
        model_class = get_shogun_model_class(csv_type)
        return self.db.query(model_class).count()

    def get_column_mapping(self, csv_type: str) -> dict[str, str]:
        """
        YAMLから日本語→英語のカラムマッピングを取得

        Args:
            csv_type: CSV種別

        Returns:
            {'伝票日付': 'slip_date', ...}
        """
        return self.table_gen.get_column_mapping(csv_type)
