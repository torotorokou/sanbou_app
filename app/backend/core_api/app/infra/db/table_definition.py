"""
テーブル定義ユーティリティ

shogun_csv_masters.yaml から動的にテーブル定義を生成するユーティリティ。
YAMLファイルを唯一の真（Single Source of Truth）として扱う。
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class TableDefinitionGenerator:
    """YAMLからテーブル定義を生成するクラス"""

    # 型マッピング: YAML type → SQLAlchemy type
    TYPE_MAPPING = {
        "datetime": "Date",
        "date": "Date",
        "str": "String",
        "int": "Integer",
        "Int64": "Integer",
        "float": "Numeric",
        "bool": "Boolean",
    }

    def __init__(self, yaml_path: Optional[str] = None):
        """
        初期化

        Args:
            yaml_path: YAMLファイルのパス（Noneの場合は環境変数またはデフォルト値を使用）
        """
        if yaml_path is None:
            # 環境変数から読み込む、なければデフォルトパスを使用
            import os

            yaml_path = os.getenv(
                "CSV_MASTERS_YAML_PATH",
                "/backend/config/csv_config/shogun_csv_masters.yaml",
            )
        self.yaml_path = yaml_path
        self.config = self._load_yaml()

    def _load_yaml(self) -> Dict[str, Any]:
        """YAMLファイルを読み込む"""
        with open(self.yaml_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def get_csv_types(self) -> List[str]:
        """
        定義されているCSV種別のリストを取得

        Returns:
            ['shipment', 'receive', 'yard'] など
        """
        # アップロード対象のCSV種別のみ（payable, sales_summaryは除外）
        upload_types = ["shipment", "receive", "yard"]
        return [k for k in self.config.keys() if k in upload_types]

    def get_table_name(self, csv_type: str, schema: str = "raw") -> str:
        """
        CSV種別からテーブル名を生成

        Args:
            csv_type: CSV種別（'receive', 'yard', 'shipment'）
            schema: スキーマ名

        Returns:
            完全修飾テーブル名（例: 'stg.shogun_flash_receive'）
        """
        table_name = f"shogun_flash_{csv_type}"
        return f"{schema}.{table_name}"

    def get_columns_definition(self, csv_type: str) -> List[Dict[str, Any]]:
        """
        CSV種別のカラム定義を取得

        Args:
            csv_type: CSV種別

        Returns:
            カラム定義のリスト
            [{
                'jp_name': '伝票日付',
                'en_name': 'slip_date',
                'type': 'Date',
                'nullable': True,
                'comment': '伝票日付'
            }, ...]
        """
        csv_config = self.config.get(csv_type, {})
        columns_config = csv_config.get("columns", {})

        columns = []
        for jp_name, col_meta in columns_config.items():
            en_name = col_meta.get("en_name")
            yaml_type = col_meta.get("type", "str")

            # 型変換
            sql_type = self.TYPE_MAPPING.get(yaml_type, "String")

            columns.append(
                {
                    "jp_name": jp_name,
                    "en_name": en_name,
                    "type": sql_type,
                    "nullable": True,  # 基本的にnullable
                    "comment": jp_name,
                    "agg": col_meta.get("agg"),
                }
            )

        return columns

    def get_expected_headers(self, csv_type: str) -> List[str]:
        """
        必須ヘッダーを取得

        Args:
            csv_type: CSV種別

        Returns:
            必須ヘッダーのリスト
        """
        csv_config = self.config.get(csv_type, {})
        return csv_config.get("expected_headers", [])

    def get_unique_keys(self, csv_type: str) -> List[str]:
        """
        一意キー（日本語）を取得

        Args:
            csv_type: CSV種別

        Returns:
            一意キーのリスト（日本語カラム名）
        """
        csv_config = self.config.get(csv_type, {})
        return csv_config.get("unique_keys", [])

    def get_unique_keys_en(self, csv_type: str) -> List[str]:
        """
        一意キー（英語）を取得

        Args:
            csv_type: CSV種別

        Returns:
            一意キーのリスト（英語カラム名）
        """
        csv_config = self.config.get(csv_type, {})
        return csv_config.get("unique_keys_en", [])

    def generate_index_columns(self, csv_type: str) -> List[str]:
        """
        インデックスを作成すべきカラムを推奨

        Args:
            csv_type: CSV種別

        Returns:
            インデックス対象カラム名（英語）のリスト
        """
        # 基本的に以下をインデックス化
        # - slip_date (伝票日付)
        # - vendor_cd (業者CD)
        # - item_cd (品名CD)
        # - その他の頻繁に検索されるキー

        columns = self.get_columns_definition(csv_type)
        index_candidates = [
            "slip_date",
            "vendor_cd",
            "item_cd",
            "client_cd",
            "shipment_no",
            "receive_no",
            "slip_no",
        ]

        en_names = [col["en_name"] for col in columns]
        return [col for col in index_candidates if col in en_names]

    def get_column_mapping(self, csv_type: str) -> Dict[str, str]:
        """
        日本語→英語のカラムマッピングを取得

        Args:
            csv_type: CSV種別

        Returns:
            {'伝票日付': 'slip_date', ...}
        """
        columns = self.get_columns_definition(csv_type)
        return {col["jp_name"]: col["en_name"] for col in columns}

    def get_type_mapping(self, csv_type: str) -> Dict[str, str]:
        """
        カラム名（英語）→型のマッピングを取得

        Args:
            csv_type: CSV種別

        Returns:
            {'slip_date': 'Date', 'net_weight': 'Numeric', ...}
        """
        columns = self.get_columns_definition(csv_type)
        return {col["en_name"]: col["type"] for col in columns}

    def generate_migration_sql(self, csv_type: str, schema: str = "raw") -> str:
        """
        マイグレーション用のCREATE TABLE SQLを生成

        Args:
            csv_type: CSV種別
            schema: スキーマ名

        Returns:
            CREATE TABLE文
        """
        table_name = f"{csv_type}_shogun_flash"
        columns = self.get_columns_definition(csv_type)

        sql_parts = [f"CREATE TABLE {schema}.{table_name} ("]
        sql_parts.append("    id SERIAL PRIMARY KEY,")

        for col in columns:
            nullable = "NULL" if col["nullable"] else "NOT NULL"
            comment = f" -- {col['comment']}" if col["comment"] else ""
            sql_parts.append(f"    {col['en_name']} {col['type']} {nullable},{comment}")

        # 共通カラム
        sql_parts.append("    raw_data_json JSONB NULL, -- 元データJSON")
        sql_parts.append(
            "    uploaded_at TIMESTAMP NOT NULL DEFAULT NOW(), -- アップロード日時"
        )
        sql_parts.append("    created_at TIMESTAMP NOT NULL DEFAULT NOW() -- 作成日時")
        sql_parts.append(");")

        return "\n".join(sql_parts)


# シングルトンインスタンス
_generator_instance: Optional[TableDefinitionGenerator] = None


def get_table_definition_generator(
    yaml_path: str = "/backend/config/csv_config/shogun_csv_masters.yaml",
) -> TableDefinitionGenerator:
    """テーブル定義ジェネレーターのシングルトンインスタンスを取得"""
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = TableDefinitionGenerator(yaml_path)
    return _generator_instance
