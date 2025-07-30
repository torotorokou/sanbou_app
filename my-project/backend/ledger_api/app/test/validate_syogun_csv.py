import requests

API_URL = "http://localhost:8001/report/manage"  # ←エンドポイントが正しければOK

files = {
    "shipment": (
        "出荷一覧.csv",
        open("/backend/app/data/csv/出荷一覧_20240501.csv", "rb"),
        "text/csv",
    ),
    # "receive": (
    #     "受入一覧.csv",
    #     open("/backend/app/data/csv/受入一覧_20250501.csv", "rb"),
    #     "text/csv",
    # ),
    "yard": (
        "ヤード一覧.csv",
        open("/backend/app/data/csv/ヤード一覧_20240501.csv", "rb"),
        "text/csv",
    ),
}

data = {
    "report_key": "factory",  # "shipment"や"yard"など
}


def main():
    response = requests.post(API_URL, files=files, data=data)
    print(f"Status: {response.status_code}")

    try:
        print("JSON response:")
        print(response.json())
    except requests.exceptions.JSONDecodeError:
        print("JSONとして読み込めません。以下が生のレスポンス本文です：")
        print(response.text)


if __name__ == "__main__":
    main()
