"""
Shogun Flash CSV Row Validation Models

将軍速報版CSVの行単位バリデーション用Pydanticモデル。
shogun_csv_masters.yaml の定義に準拠し、型安全性とバリデーションを提供。

config_loader から YAML を読み込んで動的にモデルを生成します。
"""

from datetime import datetime
from typing import Any, Optional

from backend_shared.config.config_loader import ShogunCsvConfigLoader
from pydantic import BaseModel, ConfigDict, Field, create_model, field_validator

# 型マッピング: YAML の type 文字列 → Python 型
TYPE_MAP = {
    "datetime": datetime,
    "str": str,
    "int": int,
    "Int64": int,  # pandas の Int64 は Python の int として扱う
    "float": float,
}


def parse_datetime_field(v: Any) -> Optional[datetime]:
    """日付文字列をdatetimeに変換するバリデータ関数"""
    if v is None or v == "":
        return None
    if isinstance(v, datetime):
        return v
    if isinstance(v, str):
        # 複数の日付フォーマットに対応
        for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"]:
            try:
                return datetime.strptime(v.strip(), fmt)
            except ValueError:
                continue
    raise ValueError(f"Invalid datetime format: {v}")


def create_flash_row_model(sheet_type: str) -> type[BaseModel]:
    """
    YAML定義から動的にPydanticモデルを生成する

    Args:
        sheet_type (str): CSV種別 ('receive', 'shipment', 'yard')

    Returns:
        type[BaseModel]: 生成されたPydanticモデルクラス

    Example:
        >>> model_cls = create_flash_row_model("receive")
        >>> row = {"slip_date": "2025-11-12", "vendor_cd": 123, ...}
        >>> validated = model_cls(**row)
    """
    loader = ShogunCsvConfigLoader()

    # 必須カラム（expected_headers に含まれるカラムの日本語名）
    expected_headers_jp = loader.get_expected_headers(sheet_type)

    # 英語名マップと型マップを取得
    en_name_map = loader.get_en_name_map(sheet_type)

    # 必須カラムの英語名セットを作成
    required_en_names = {
        en_name_map[jp_name]
        for jp_name in expected_headers_jp
        if jp_name in en_name_map
    }

    # フィールド定義を構築
    field_definitions = {}
    datetime_fields = []

    for jp_name, meta in loader.get_columns(sheet_type).items():
        en_name = meta.get("en_name")
        type_str = meta.get("type")

        if not en_name or not type_str:
            continue

        # Python型に変換
        py_type = TYPE_MAP.get(type_str, str)

        # 必須かどうかを判定
        is_required = en_name in required_en_names

        # datetime 型のフィールドは後でバリデータを追加
        if py_type == datetime:
            datetime_fields.append(en_name)
            if is_required:
                field_definitions[en_name] = (datetime, Field(..., description=jp_name))
            else:
                field_definitions[en_name] = (
                    Optional[datetime],
                    Field(None, description=jp_name),
                )
        else:
            if is_required:
                field_definitions[en_name] = (py_type, Field(..., description=jp_name))
            else:
                field_definitions[en_name] = (
                    Optional[py_type],
                    Field(None, description=jp_name),
                )

    # モデルを動的生成
    model_name = f"{sheet_type.capitalize()}FlashRow"
    DynamicModel = create_model(
        model_name,
        __config__=ConfigDict(str_strip_whitespace=True, arbitrary_types_allowed=True),
        **field_definitions,
    )

    # datetime フィールドにバリデータを追加
    if datetime_fields:
        # バリデータをデコレータとして追加
        for dt_field in datetime_fields:
            validator_func = field_validator(dt_field, mode="before")(
                lambda cls, v, _field=dt_field: parse_datetime_field(v)
            )
            # モデルにバリデータを登録
            if not hasattr(DynamicModel, "__pydantic_decorators__"):
                DynamicModel.__pydantic_decorators__ = type(
                    "Decorators", (), {"field_validators": {}}
                )()

    return DynamicModel


# 各CSV種別のモデルを生成してエクスポート
ReceiveFlashRow = create_flash_row_model("receive")
ShipmentFlashRow = create_flash_row_model("shipment")
YardFlashRow = create_flash_row_model("yard")
