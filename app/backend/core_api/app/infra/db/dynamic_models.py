"""
動的ORM モデルジェネレーター

syogun_csv_masters.yaml からSQLAlchemy ORMモデルを動的に生成します。

クラス名衝突を回避するため、同一クラス名の再生成を抑止します。
"""

from sqlalchemy import Column, Integer, String, Date, Numeric, Text, TIMESTAMP, JSON, Time, func, Table, MetaData
from sqlalchemy.orm import declarative_base, registry
from sqlalchemy.sql.type_api import TypeEngine
from typing import Type, Dict, Any, Union, Callable
import logging

from app.infra.db.table_definition import get_table_definition_generator

logger = logging.getLogger(__name__)

Base = declarative_base()
mapper_registry = registry()

# 動的に生成されたモデルクラスのレジストリ（クラス名衝突を防ぐ）
_dynamic_model_registry: Dict[str, Type] = {}


def create_shogun_model_class(csv_type: str, table_name: str | None = None, schema: str = "raw") -> Type:
    """
    CSV種別からORMモデルクラスを動的に生成
    
    Args:
        csv_type: CSV種別（'receive', 'yard', 'shipment'）
        table_name: テーブル名（省略時は '{csv_type}_shogun_flash'）
        schema: スキーマ名（デフォルト: 'raw'）
        
    Returns:
        動的に生成されたORMモデルクラス
    """
    generator = get_table_definition_generator()
    actual_table_name = table_name or f"{csv_type}_shogun_flash"
    columns_def = generator.get_columns_definition(csv_type)
    
    # SQLAlchemy ORMモデルクラスの属性を準備
    attrs: Dict[str, Any] = {
        '__tablename__': actual_table_name,  # DBテーブル名
        '__table_args__': {
            'schema': schema,  # スキーマ名 (raw, debug等)
            'extend_existing': True,  # 既存テーブル定義を上書き許可
        },
    }
    
    # YAML型定義 → SQLAlchemy型のマッピング
    TYPE_MAPPING: Dict[str, Union[Type[TypeEngine[Any]], Callable[[], Any]]] = {
        'String': String,
        'Integer': Integer,
        'Int64': Integer,  # pandas nullable Int64 → SQLAlchemy Integer
        'int': Integer,    # YAML 'int' → SQLAlchemy Integer
        'Numeric': Numeric,
        'Date': Date,
        'datetime': Date,  # YAML 'datetime' → SQLAlchemy Date
        'Boolean': lambda: lambda: None,  # 未使用
    }
    
    # 全カラムを通常列として追加し、後で複合主キーとして指定
    # 理由: SQLAlchemyは主キーが必須だが、DBテーブルには主キーがないため、
    #       全列を複合主キーとして扱うことでINSERT時に全値を送信
    primary_key_cols = []
    
    for col in columns_def:
        col_type_str = col['type']
        col_name = col['en_name']
        
        # カラム名に "time" が含まれる場合は Time 型を使用（weighing_time 等）
        if "time" in col_name.lower() and "date" not in col_name.lower():
            col_instance = Time()
        else:
            # YAML定義の型をSQLAlchemy型に変換
            col_type_class = TYPE_MAPPING.get(col_type_str, String)
            
            if callable(col_type_class) and col_type_str != 'Boolean':
                col_instance = col_type_class()  # type: ignore
            else:
                col_instance = String()  # フォールバック
        
        # カラムオブジェクトを作成（primary_key=False）
        col_obj = Column(
            col_instance,
            nullable=col['nullable'],
            comment=col['comment']
        )
        attrs[col_name] = col_obj
        primary_key_cols.append(col_obj)  # 複合主キー用リストに追加
    
    # SQLAlchemyのマッパー設定: 全列を複合主キーとして指定
    # これによりINSERT時にすべての列が含まれる（主キー自動除外を回避）
    attrs['__mapper_args__'] = {
        'primary_key': primary_key_cols
    }
    
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
ReceiveShogunFlash = get_shogun_model_class('receive')
YardShogunFlash = get_shogun_model_class('yard')
ShipmentShogunFlash = get_shogun_model_class('shipment')
