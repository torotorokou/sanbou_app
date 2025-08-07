#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Block Unit Price Interactive API のテスト用クライアントスクリプト

実際のAPIエンドポイントをテストし、デバッグすることができます。
"""

import io
import json
from typing import Any, Dict

import pandas as pd
import requests


class BlockUnitPriceAPIClient:
    """Block Unit Price Interactive API のクライアント"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api/block-unit-price-interactive"

    def create_test_csv_files(self) -> Dict[str, io.StringIO]:
        """テスト用CSVファイルを作成"""
        # 出荷データ
        shipment_data = {
            "業者名": ["業者A", "業者B", "業者C", "業者A", "業者B"],
            "業者CD": ["001", "002", "003", "001", "002"],
            "品名": ["商品1", "商品2", "商品3", "商品4", "商品5"],
            "明細備考": ["備考1", "備考2", "備考3", "備考4", "備考5"],
            "単価": [100, 200, 150, 300, 250],
            "数量": [10, 5, 8, 12, 6],
            "正味重量": [50, 25, 40, 60, 30],
            "単位名": ["kg", "kg", "台", "kg", "kg"],
            "伝票日付": [
                "2025-08-06",
                "2025-08-06",
                "2025-08-06",
                "2025-08-06",
                "2025-08-06",
            ],
        }

        # ヤードデータ
        yard_data = {"項目": ["A", "B", "C"], "値": [1, 2, 3]}

        # 受入データ
        receive_data = {"項目": ["X", "Y", "Z"], "値": [10, 20, 30]}

        files = {}
        for name, data in [
            ("shipment", shipment_data),
            ("yard", yard_data),
            ("receive", receive_data),
        ]:
            df = pd.DataFrame(data)
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False, encoding="utf-8")
            csv_buffer.seek(0)
            files[name] = csv_buffer

        return files

    def step_1_upload_and_start(self) -> Dict[str, Any]:
        """Step 1: ファイルアップロードと処理開始"""
        print("=== Step 1: ファイルアップロードと処理開始 ===")

        files = self.create_test_csv_files()

        # ファイルアップロード用のデータを準備
        files_data = {}
        for name, csv_buffer in files.items():
            files_data[f"{name}_file"] = (
                f"{name}.csv",
                csv_buffer.getvalue(),
                "text/csv",
            )

        try:
            response = requests.post(
                f"{self.api_url}/upload-and-start", files=files_data, timeout=30
            )
            response.raise_for_status()

            result = response.json()
            print(f"ステータス: {result.get('status')}")
            print(f"メッセージ: {result.get('message')}")

            if result.get("status") == "success":
                transport_options = result["data"]["transport_options"]
                print(f"運搬業者選択肢数: {len(transport_options)}")
                print("最初の3つの選択肢:")
                for option in transport_options[:3]:
                    print(f"  - {option}")

            return result

        except requests.exceptions.RequestException as e:
            print(f"API呼び出しエラー: {e}")
            return {"status": "error", "message": str(e)}

    def step_2_select_transport(self, session_id: str) -> Dict[str, Any]:
        """Step 2: 運搬業者選択"""
        print("\n=== Step 2: 運搬業者選択 ===")

        # サンプル選択データ
        selections = {"業者A": "運搬A", "業者B": "運搬B", "業者C": "運搬C"}

        payload = {"session_id": session_id, "selections": selections}

        try:
            response = requests.post(
                f"{self.api_url}/select-transport",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )
            response.raise_for_status()

            result = response.json()
            print(f"ステータス: {result.get('status')}")
            print(f"メッセージ: {result.get('message')}")

            if result.get("status") == "success":
                summary = result["data"].get("selection_summary", {})
                print(f"選択サマリー: {summary}")

            return result

        except requests.exceptions.RequestException as e:
            print(f"API呼び出しエラー: {e}")
            return {"status": "error", "message": str(e)}

    def step_3_finalize_calculation(
        self, session_id: str, confirmed: bool = True
    ) -> Dict[str, Any]:
        """Step 3: 計算の最終確定"""
        print("\n=== Step 3: 計算の最終確定 ===")

        payload = {"session_id": session_id, "confirmed": confirmed}

        try:
            response = requests.post(
                f"{self.api_url}/finalize",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )
            response.raise_for_status()

            result = response.json()
            print(f"ステータス: {result.get('status')}")
            print(f"メッセージ: {result.get('message')}")

            if result.get("status") == "completed":
                data = result["data"]
                summary = data.get("summary", {})
                print(f"計算結果サマリー: {summary}")

                # 結果CSVの情報
                if "result_csv" in data:
                    result_csv = data["result_csv"]
                    print(f"結果CSV行数: {len(result_csv)}")

            return result

        except requests.exceptions.RequestException as e:
            print(f"API呼び出しエラー: {e}")
            return {"status": "error", "message": str(e)}

    def get_status(self, session_id: str) -> Dict[str, Any]:
        """セッション状態の確認"""
        print(f"\n=== セッション状態確認: {session_id} ===")

        try:
            response = requests.get(
                f"{self.api_url}/status", params={"session_id": session_id}, timeout=30
            )
            response.raise_for_status()

            result = response.json()
            print(f"ステータス: {result.get('status')}")
            print(f"メッセージ: {result.get('message')}")

            return result

        except requests.exceptions.RequestException as e:
            print(f"API呼び出しエラー: {e}")
            return {"status": "error", "message": str(e)}

    def test_full_workflow(self):
        """完全なワークフローのテスト"""
        print("Block Unit Price Interactive API の完全ワークフローテストを開始")
        print("=" * 60)

        try:
            # Step 1: ファイルアップロードと処理開始
            result1 = self.step_1_upload_and_start()
            if result1.get("status") != "success":
                print("Step 1 が失敗したためテストを終了します")
                return result1

            session_id = result1["data"]["session_id"]
            print(f"セッションID: {session_id}")

            # セッション状態確認
            self.get_status(session_id)

            # Step 2: 運搬業者選択
            result2 = self.step_2_select_transport(session_id)
            if result2.get("status") != "success":
                print("Step 2 が失敗したためテストを終了します")
                return result2

            # Step 3: 計算の最終確定
            result3 = self.step_3_finalize_calculation(session_id, confirmed=True)

            print("\n" + "=" * 60)
            print("完全ワークフローテストが完了しました")

            # 結果を保存
            test_results = {
                "step_1": result1,
                "step_2": result2,
                "step_3": result3,
                "session_id": session_id,
            }

            with open("/backend/api_test_results.json", "w", encoding="utf-8") as f:
                json.dump(test_results, f, ensure_ascii=False, indent=2, default=str)

            print("テスト結果を api_test_results.json に保存しました")
            return test_results

        except Exception as e:
            print(f"テスト中にエラーが発生しました: {e}")
            import traceback

            traceback.print_exc()
            return {"status": "error", "message": str(e)}


def test_server_connection(base_url: str = "http://localhost:8000"):
    """サーバー接続テスト"""
    print(f"サーバー接続テスト: {base_url}")

    try:
        response = requests.get(f"{base_url}/docs", timeout=10)
        if response.status_code == 200:
            print("✓ サーバーが起動しており、APIドキュメントにアクセスできます")
            return True
        else:
            print(f"✗ サーバーからの応答が期待と異なります: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ サーバーに接続できません。サーバーが起動しているか確認してください")
        return False
    except requests.exceptions.Timeout:
        print("✗ サーバーからの応答がタイムアウトしました")
        return False
    except Exception as e:
        print(f"✗ 接続テスト中にエラーが発生しました: {e}")
        return False


def main():
    """メイン関数"""
    print("Block Unit Price Interactive API テスト")
    print("=" * 50)

    # サーバー接続テスト
    if not test_server_connection():
        print("\n注意: サーバーが起動していない可能性があります")
        print("以下のコマンドでサーバーを起動してください:")
        print(
            "cd /backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
        )
        return

    # APIクライアントの作成とテスト実行
    client = BlockUnitPriceAPIClient()
    results = client.test_full_workflow()

    if (
        results
        and isinstance(results, dict)
        and "step_3" in results
        and isinstance(results["step_3"], dict)
        and results["step_3"].get("status") == "completed"
    ):
        print("\n✓ 全てのテストが正常に完了しました")
    else:
        print("\n✗ テスト中に問題が発生しました")


if __name__ == "__main__":
    main()
