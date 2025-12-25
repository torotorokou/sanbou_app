"""
動的ORM モデルジェネレーター

shogun_csv_masters.yaml からSQLAlchemy ORMモデルを動的に生成します。

クラス名衝突を回避するため、同一クラス名の再生成を抑止します。
"""

import logging
from typing import Any, Callable, Dict, Type, Union

from app.infra.db.table_definition import get_table_definition_generator
from backend_shared.application.logging import create_log_context, get_module_logger
from sqlalchemy import (
    JSON,
    TIMESTAMP,
    Column,
    Date,
    Integer,
    MetaData,
    Numeric,
    String,
    Table,
    Text,
    Time,
    func,
)
from sqlalchemy.orm import declarative_base, registry
from sqlalchemy.sql.type_api import TypeEngine

logger = get_module_logger(__name__)

Base = declarative_base()
mapper_registry = registry()

# 動的に生成されたモデルクラスのレジストリ（クラス名衝突を防ぐ）
_dynamic_model_registry: Dict[str, Type] = {}


def create_shogun_model_class(
    csv_type: str, table_name: str | None = None, schema: str = "stg"
) -> Type:
    """
    CSV種別からORMモデルクラスを動的に生成

    Args:
        csv_type: CSV種別('receive', 'yard', 'shipment')
        table_name: テーブル名(省略時は '{csv_type}_shogun_flash')
        schema: スキーマ名(デフォルト: 'stg')

    Returns:
        動的に生成されたORMモデルクラス
    """
    generator = get_table_definition_generator()
    actual_table_name = table_name or f"{csv_type}_shogun_flash"
    columns_def = generator.get_columns_definition(csv_type)

    # SQLAlchemy ORMモデルクラスの属性を準備
    attrs: Dict[str, Any] = {
        "__tablename__": actual_table_name,  # DBテーブル名
        "__table_args__": {
            "schema": schema,  # スキーマ名 (raw, debug等)
            "extend_existing": True,  # 既存テーブル定義を上書き許可
        },
    }

    # YAML型定義 → SQLAlchemy型のマッピング
    TYPE_MAPPING: Dict[str, Union[Type[TypeEngine[Any]], Callable[[], Any]]] = {
        "String": String,
        "Integer": Integer,
        "Int64": Integer,  # pandas nullable Int64 → SQLAlchemy Integer
        "int": Integer,  # YAML 'int' → SQLAlchemy Integer
        "Numeric": Numeric,
        "Date": Date,
        "datetime": Date,  # YAML 'datetime' → SQLAlchemy Date
        "Boolean": lambda: lambda: None,  # 未使用
    }

    # まず id カラムを主キーとして追加（実テーブルの主キー）
    # これによりSQLAlchemyが正しく動作する
    attrs["id"] = Column(
        Integer, primary_key=True, autoincrement=True, comment="Primary key"
    )

    # 各YAMLカラムを通常列として追加
    for col in columns_def:
        col_type_str = col["type"]
        col_name = col["en_name"]

        # raw層は全カラムをTEXT型として扱う（生データ保存用）
        if schema == "raw":
            col_instance = Text()
            logger.debug(f"[{schema}] {col_name}: TEXT (raw layer)")
        # stg層以降はYAMLの型定義を使用（型付きデータ保存用）
        elif "time" in col_name.lower() and "date" not in col_name.lower():
            # カラム名に "time" が含まれる場合は Time 型を使用（weighing_time 等）
            col_instance = Time()
        else:
            # YAML定義の型をSQLAlchemy型に変換
            col_type_class = TYPE_MAPPING.get(col_type_str, String)

            if callable(col_type_class) and col_type_str != "Boolean":
                col_instance = col_type_class()  # type: ignore
            else:
                col_instance = String()  # フォールバック

        # カラムオブジェクトを作成（通常列として）
        col_obj = Column(col_instance, nullable=col["nullable"], comment=col["comment"])
        attrs[col_name] = col_obj

    # トラッキングカラムを追加（upload_file_id, source_row_no, created_at）
    # これらはYAML定義外だが、全テーブルに共通で存在する
    tracking_cols = [
        (
            "upload_file_id",
            Integer,
            "アップロード元ファイルID (log.upload_file.id への参照)",
        ),
        ("source_row_no", Integer, "CSV元行番号（1-indexed）"),
    ]

    for col_name, col_type, col_comment in tracking_cols:
        col_obj = Column(col_type(), nullable=True, comment=col_comment)
        attrs[col_name] = col_obj

    # created_at カラムを追加（タイムスタンプ用）
    attrs["created_at"] = Column(
        TIMESTAMP(timezone=True),
        nullable=True,
        server_default=func.now(),
        comment="レコード作成日時",
    )

    # 動的クラス名: {csv_type}_{schema}_{table_name}
    class_name = f"{csv_type.capitalize()}_{schema}_{actual_table_name}"

    # キャッシュされたモデルがあれば再利用
    if class_name in _dynamic_model_registry:
        return _dynamic_model_registry[class_name]

    # type()を使用して動的にORMモデルクラスを生成
    model_class = type(class_name, (Base,), attrs)

    # レジストリに登録して再利用可能にする
    _dynamic_model_registry[class_name] = model_class

    return model_class


# 事前に生成したモデルをキャッシュ
_model_cache: Dict[str, Type] = {}


def clear_model_cache():
    """モデルキャッシュをクリア（デバッグ用）"""
    global _model_cache, _dynamic_model_registry
    _model_cache.clear()
    _dynamic_model_registry.clear()
    logger.info("Model cache cleared")


def get_shogun_model_class(csv_type: str, schema: str = "raw") -> Type:
    """
    CSV種別からORMモデルクラスを取得（キャッシュ付き）

    Args:
        csv_type: CSV種別
        schema: スキーマ名（デフォルト: 'raw'）

    Returns:
        ORMモデルクラス
    """
    cache_key = f"{csv_type}_{schema}"
    if cache_key not in _model_cache:
        _model_cache[cache_key] = create_shogun_model_class(csv_type, schema=schema)
    return _model_cache[cache_key]


# 後方互換性のため、静的モデルも定義（非推奨）
ReceiveShogunFlash = get_shogun_model_class("receive")
YardShogunFlash = get_shogun_model_class("yard")
ShipmentShogunFlash = get_shogun_model_class("shipment")
