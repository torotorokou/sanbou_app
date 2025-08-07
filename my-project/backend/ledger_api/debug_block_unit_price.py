#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ブロック単価計算のデバッグ用スクリプト

このスクリプトはVSCodeのデバッグ機能を使って
Block Unit Price Interactive の処理をステップ実行できます。
"""

import json
import sys

import pandas as pd

# パスの設定
sys.path.append("/backend")
sys.path.append("/backend/backend_shared/src")

from app.api.st_app.logic.manage.block_unit_price_interactive import (
    BlockUnitPriceInteractive,
)


def create_mock_dataframes():
    """デバッグ用のモックデータを作成"""
    # 出荷データのサンプル
    shipment_data = pd.read_csv("/backend/app/data/csv/出荷一覧_20240501.csv")

    return {
        "shipment": pd.DataFrame(shipment_data),
        # "yard": pd.DataFrame(yard_data),
        # "receive": pd.DataFrame(receive_data),
    }


def debug_step_0_initialization():
    """Step 0: 初期処理のデバッグ"""
    print("=== Step 0: 初期処理のデバッグ ===")

    # モックデータの作成
    dfs = create_mock_dataframes()
    print(f"作成されたデータフレーム: {list(dfs.keys())}")
    print(f"出荷データ形状: {dfs['shipment'].shape}")
    print("\n出荷データサンプル:")
    print(dfs["shipment"].head())

    # ブロック単価計算処理の初期化
    processor = BlockUnitPriceInteractive()

    # ここにブレークポイントを設定してデバッグ
    result = processor.start_process(dfs)

    print(f"\n初期処理結果のステータス: {result.get('status')}")
    print(f"メッセージ: {result.get('message')}")

    if result.get("status") == "success":
        transport_options = result["data"]["transport_options"]
        print(f"\n運搬業者選択肢数: {len(transport_options)}")
        print("運搬業者選択肢:")
        for option in transport_options[:]:  # 最初の3つを表示
            print(f"  - {option}")

    return result


def debug_step_1_transport_selection(initial_result):
    """Step 1: 運搬業者選択のデバッグ"""
    print("\n=== Step 1: 運搬業者選択のデバッグ ===")

    if initial_result.get("status") != "success":
        print("初期処理が成功していないためスキップします")
        return None

    # セッションデータの取得
    session_data = initial_result["data"]["session_data"]

    # 運搬業者選択のサンプル（実際のフロントエンドからの選択をシミュレート）
    selections = {"業者A": "運搬A", "業者B": "運搬B", "業者C": "運搬C"}

    print(f"選択データ: {selections}")

    # 処理実行
    processor = BlockUnitPriceInteractive()

    # ここにブレークポイントを設定してデバッグ
    result = processor.process_selection(session_data, selections)

    print(f"\n選択処理結果のステータス: {result.get('status')}")
    print(f"メッセージ: {result.get('message')}")

    if result.get("status") == "success":
        summary = result["data"]["selection_summary"]
        print(f"\n選択サマリー: {summary}")

    return result


def debug_step_2_finalization(selection_result):
    """Step 2: 最終計算のデバッグ"""
    print("\n=== Step 2: 最終計算のデバッグ ===")

    if selection_result.get("status") != "success":
        print("運搬業者選択処理が成功していないためスキップします")
        return None

    # セッションデータの取得
    session_data = selection_result["data"]["session_data"]

    # 処理実行
    processor = BlockUnitPriceInteractive()

    # ここにブレークポイントを設定してデバッグ
    result = processor.finalize_calculation(session_data, confirmed=True)

    print(f"\n最終計算結果のステータス: {result.get('status')}")
    print(f"メッセージ: {result.get('message')}")

    if result.get("status") == "completed":
        data = result["data"]
        print(f"\n計算結果サマリー: {data.get('summary', {})}")

        if "result_csv" in data:
            result_csv = data["result_csv"]
            print(f"結果CSV行数: {len(result_csv)}")
            if result_csv:
                print("結果CSVサンプル:")
                for i, row in enumerate(result_csv[:3]):
                    print(f"  行{i + 1}: {row}")

    return result


def main():
    """メインデバッグ処理"""
    print("ブロック単価計算のデバッグを開始します")
    print("=" * 50)

    try:
        # Step 0: 初期処理
        initial_result = debug_step_0_initialization()

        # Step 1: 運搬業者選択
        selection_result = debug_step_1_transport_selection(initial_result)

        # Step 2: 最終計算
        final_result = debug_step_2_finalization(selection_result)

        print("\n" + "=" * 50)
        print("デバッグ処理が完了しました")

        # 結果をJSONファイルに保存
        debug_results = {
            "step_0": initial_result,
            "step_1": selection_result,
            "step_2": final_result,
        }

        with open("/backend/debug_results.json", "w", encoding="utf-8") as f:
            json.dump(debug_results, f, ensure_ascii=False, indent=2, default=str)

        print("デバッグ結果を debug_results.json に保存しました")

    except Exception as e:
        print(f"デバッグ中にエラーが発生しました: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
