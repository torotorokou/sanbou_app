#!/usr/bin/env python3
"""
shogun_flash_schemas.py の動作確認テスト

YAML から動的生成されたモデルが正しく動作するか検証します。
"""

import sys
from pathlib import Path

from pydantic import ValidationError

# パスを追加（backend_shared と core_api をインポート可能にする）
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path / "backend_shared" / "src"))
sys.path.insert(0, str(backend_path / "core_api"))

# ローカル実行用にパスを上書き
import backend_shared.infrastructure.config.paths as paths_module  # noqa: E402

paths_module.SHOGUNCSV_DEF_PATH = str(
    backend_path.parent / "config" / "csv_config" / "shogun_csv_masters.yaml"
)

from app.core.domain.shogun_flash_schemas import (  # noqa: E402
    ReceiveFlashRow,
    ShipmentFlashRow,
    YardFlashRow,
)


def test_receive_flash_row():
    """受入一覧モデルのテスト"""
    print("=" * 60)
    print("受入一覧モデル (ReceiveFlashRow) のテスト")
    print("=" * 60)

    # 正常ケース（必須フィールドのみ）
    valid_row = {
        "slip_date": "2025-11-12",
        "vendor_cd": 123,
        "item_cd": 456,
        "receive_no": 789,
        "net_weight": 100.5,
    }

    try:
        model = ReceiveFlashRow(**valid_row)
        print("✓ 必須フィールドのみ: 成功")
        print(f"  slip_date type: {type(model.slip_date)}")
        print(f"  slip_date value: {model.slip_date}")
    except ValidationError as e:
        print(f"✗ 必須フィールドのみ: 失敗\n{e}")

    # 必須フィールドが不足しているケース
    invalid_row = {
        "slip_date": "2025-11-12",
        "vendor_cd": 123,
        # item_cd が欠けている
    }

    try:
        model = ReceiveFlashRow(**invalid_row)
        print("✗ 必須フィールド不足: 検証エラーが出なかった（バグの可能性）")
    except ValidationError as e:
        print("✓ 必須フィールド不足: 正しくエラーが出た")
        print(f"  エラー内容: {e.error_count()} 件")

    # 任意フィールドを含むケース
    full_row = {
        "slip_date": "2025-11-12",
        "sales_date": "2025/11/13",
        "payment_date": "20251114",
        "vendor_cd": 123,
        "vendor_name": "テスト業者",
        "item_cd": 456,
        "item_name": "テスト品名",
        "receive_no": 789,
        "net_weight": 100.5,
        "quantity": 2.0,
        "unit_name": "kg",
    }

    try:
        model = ReceiveFlashRow(**full_row)
        print("✓ 任意フィールド含む: 成功")
        print(f"  sales_date: {model.sales_date}")
        print(f"  payment_date: {model.payment_date}")
    except ValidationError as e:
        print(f"✗ 任意フィールド含む: 失敗\n{e}")

    print()


def test_shipment_flash_row():
    """出荷一覧モデルのテスト"""
    print("=" * 60)
    print("出荷一覧モデル (ShipmentFlashRow) のテスト")
    print("=" * 60)

    # 正常ケース
    valid_row = {
        "slip_date": "2025-11-12",
        "shipment_no": "SH001",
        "client_en_name": "取引先A",
        "vendor_cd": 123,
        "vendor_en_name": "業者B",
        "item_en_name": "品名C",
        "net_weight": 50.0,
        "quantity": 10.0,
    }

    try:
        model = ShipmentFlashRow(**valid_row)
        print("✓ 必須フィールド: 成功")
        print(f"  shipment_no: {model.shipment_no}")
    except ValidationError as e:
        print(f"✗ 必須フィールド: 失敗\n{e}")

    print()


def test_yard_flash_row():
    """ヤード一覧モデルのテスト"""
    print("=" * 60)
    print("ヤード一覧モデル (YardFlashRow) のテスト")
    print("=" * 60)

    # 正常ケース
    valid_row = {
        "slip_date": "2025-11-12",
        "client_en_name": "取引先X",
        "item_en_name": "品名Y",
        "net_weight": 200.0,
        "quantity": 5.0,
        "vendor_cd": 999,
        "vendor_en_name": "業者Z",
        "item_cd": 111,
    }

    try:
        model = YardFlashRow(**valid_row)
        print("✓ 必須フィールド: 成功")
        print(f"  item_cd: {model.item_cd}")
    except ValidationError as e:
        print(f"✗ 必須フィールド: 失敗\n{e}")

    print()


if __name__ == "__main__":
    test_receive_flash_row()
    test_shipment_flash_row()
    test_yard_flash_row()
    print("=" * 60)
    print("テスト完了")
    print("=" * 60)
