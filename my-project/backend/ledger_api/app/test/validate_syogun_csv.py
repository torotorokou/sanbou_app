"""
昇軍CSVバリデーションテスト

帳票管理APIに対してCSVファイルをアップロードし、
レスポンスの検証を行うテストスクリプトです。
"""

import requests

# APIエンドポイントURL
API_URL = "http://localhost:8001/report/manage"

# テスト用CSVファイルの設定
files = {
    "shipment": (
        "出荷一覧.csv",
        open("/backend/app/data/csv/出荷一覧_20240501.csv", "rb"),
        "text/csv",
    ),
    "yard": (
        "ヤード一覧.csv",
        open("/backend/app/data/csv/ヤード一覧_20240501.csv", "rb"),
        "text/csv",
    ),
}

# リクエストデータ
data = {
    "report_key": "factory_report",  # 帳票タイプキー
}


def main():
    """
    メイン処理

    APIにCSVファイルをアップロードし、レスポンスを処理します。
    成功時はファイルを保存し、エラー時はエラー内容を表示します。
    """
    # APIリクエストを送信
    response = requests.post(API_URL, files=files, data=data)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        # 成功時の処理：ファイル保存

        # ファイル名をContent-Dispositionヘッダーから取得（なければデフォルト名）
        file_name = "output.xlsx"
        cd = response.headers.get("Content-Disposition")

        if cd:
            import re
            import urllib.parse

            # ファイル名パターン（UTF-8エンコード）: filename*=UTF-8''xxxx.xlsx
            m = re.search(r"filename\*\=UTF-8''([^;]+)", cd)
            if m:
                file_name = urllib.parse.unquote(m.group(1))
            else:
                # ファイル名パターン（クォート付き）: filename="xxxx.xlsx"
                m = re.search(r'filename="([^"]+)"', cd)
                if m:
                    file_name = m.group(1)

        # レスポンス内容をファイルに保存
        with open(file_name, "wb") as f:
            f.write(response.content)
        print(f"Excelファイルを保存しました: {file_name}")
    else:
        # エラー時の処理：エラー内容表示
        print("エラー発生:")
        print(response.text)


if __name__ == "__main__":
    main()
