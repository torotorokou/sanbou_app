"""
動的ORM モデルジェネレーター

syogun_csv_masters.yaml からSQLAlchemy ORMモデルを動的に生成します。
"""

from sqlalchemy import Column, Integer, String, Date, Numeric, Text, TIMESTAMP, JSON, func
from sqlalchemy.orm import declarative_base
from typing import Type, Dict, Any

from app.config.table_definition import get_table_definition_generator

Base = declarative_base()


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
    
    # クラス属性を準備
    attrs: Dict[str, Any] = {
        '__tablename__': actual_table_name,
        '__table_args__': {'schema': schema},
        'id': Column(Integer, primary_key=True, autoincrement=True),
    }
    
    # YAMLからカラムを追加
    TYPE_MAPPING = {
        'String': String,
        'Integer': Integer,
        'Numeric': Numeric,
        'Date': Date,
        'Boolean': lambda: lambda: None,  # 未使用
    }
    
    for col in columns_def:
        col_type_class = TYPE_MAPPING.get(col['type'], String)
        attrs[col['en_name']] = Column(
            col_type_class() if callable(col_type_class) else col_type_class,
            nullable=col['nullable'],
            comment=col['comment']
        )
    
    # 共通カラムを追加
    attrs['raw_data_json'] = Column(JSON, nullable=True, comment='元データJSON')
    attrs['uploaded_at'] = Column(TIMESTAMP, nullable=False, default=func.now(), comment='アップロード日時')
    attrs['created_at'] = Column(TIMESTAMP, nullable=False, default=func.now(), comment='作成日時')
    
    # 動的クラス生成
    class_name = f"{csv_type.capitalize()}ShogunFlash"
    model_class = type(class_name, (Base,), attrs)
    
    return model_class


# 事前に生成したモデルをキャッシュ
_model_cache: Dict[str, Type] = {}

def get_shogun_model_class(csv_type: str) -> Type:
    """
    CSV種別からORMモデルクラスを取得（キャッシュ付き）
    
    Args:
        csv_type: CSV種別
        
    Returns:
        ORMモデルクラス
    """
    if csv_type not in _model_cache:
        _model_cache[csv_type] = create_shogun_model_class(csv_type)
    return _model_cache[csv_type]


# 後方互換性のため、静的モデルも定義（非推奨）
ReceiveShogunFlash = get_shogun_model_class('receive')
YardShogunFlash = get_shogun_model_class('yard')
ShipmentShogunFlash = get_shogun_model_class('shipment')
