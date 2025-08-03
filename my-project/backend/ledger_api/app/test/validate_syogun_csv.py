import requests

API_URL = "http://localhost:8001/report/manage"

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

data = {
    "report_key": "factory_report",
}


def main():
    response = requests.post(API_URL, files=files, data=data)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        # ファイル名をContent-Dispositionから取得（なければデフォルト名）
        file_name = "output.xlsx"
        cd = response.headers.get("Content-Disposition")
        if cd:
            import re, urllib.parse

            # filename*=UTF-8''xxxx.xlsx
            m = re.search(r"filename\*\=UTF-8''([^;]+)", cd)
            if m:
                file_name = urllib.parse.unquote(m.group(1))
            else:
                m = re.search(r'filename="([^"]+)"', cd)
                if m:
                    file_name = m.group(1)

        with open(file_name, "wb") as f:
            f.write(response.content)
        print(f"Excelファイルを保存しました: {file_name}")
    else:
        print("エラー発生:")
        print(response.text)


if __name__ == "__main__":
    main()
