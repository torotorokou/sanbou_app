def check_csv_files(files: dict, required: list[str], optional: list[str] = None):
    """
    必須ファイル・任意ファイルを元に、アップロードCSVの有無を判定する。
    必須が足りない場合は例外を投げる。
    """
    optional = optional or []
    missing_required = set(required) - set(files.keys())
    if missing_required:
        raise ValueError(f"必要なCSVファイルが不足しています: {', '.join(missing_required)}")

    # 任意ファイルは何もせずOK
    # 利用時は files.get(name) でNoneなら「未提出」とみなせる
