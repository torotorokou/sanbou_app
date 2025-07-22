import requests

API_URL = "http://localhost:8001/upload/syogun_csv"

files = {
    "shipment": (
        "出荷一覧.csv",
        open("/backend/app/data/出荷一覧_20250604_180607.csv", "rb"),
        "text/csv",
    ),
    "receive": (
        "受入一覧.csv",
        open("/backend/app/data/受入一覧_20250604_180559.csv", "rb"),
        "text/csv",
    ),
    "yard": (
        "ヤード一覧.csv",
        open("/backend/app/data/ヤード一覧_20250604_180615.csv", "rb"),
        "text/csv",
    ),
}


def main():
    response = requests.post(API_URL, files=files)
    print(f"Status: {response.status_code}")

    try:
        print("JSON response:")
        print(response.json())
    except requests.exceptions.JSONDecodeError:
        print("JSONとして読み込めません。以下が生のレスポンス本文です：")
        print(response.text)


if __name__ == "__main__":
    main()
