import pandas as pd


# 共通の特殊値リスト（欠損値として扱う文字列）
NA_STRING_VALUES = ["<NA>", "nan", "None", "NaN", "NULL", "null", "#N/A", "#NA", ""]


def combine_date_and_time(df: pd.DataFrame, date_col: str, time_col: str) -> pd.DataFrame:
    """
    date_col（datetime64）と time_col（時刻文字列）を結合し、
    datetime64[ns] に変換して time_col に上書き。
    """

    def normalize_time_string(s: str) -> str:
        parts = s.strip().split(":")
        if len(parts) == 2:
            return s.strip() + ":00"
        return s.strip()

    # 日付 → 文字列 YYYY/MM/DD
    date_str = df[date_col].dt.strftime("%Y/%m/%d")

    # 時刻 → "HH:MM:SS" 形式に補完
    time_str = df[time_col].astype(str).map(normalize_time_string)

    # 結合して datetime 変換
    combined_str = date_str + " " + time_str
    df[time_col] = pd.to_datetime(combined_str, format="%Y/%m/%d %H:%M:%S", errors="coerce")

    # デバッグ用
    # print(df[[date_col, time_col]].head())

    return df


def remove_weekday_parentheses(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """
    指定カラムの値に曜日括弧が含まれる場合のみ、それを除去してdatetime64[ns]型に変換する。
    例: '2025/06/01(日)' → '2025/06/01' → datetime64[ns]

    :param df: 対象DataFrame
    :param column: 変換対象のカラム名
    :return: 加工済みDataFrame
    """
    mask = df[column].astype(str).str.contains(r"\([^)]+\)", regex=True, na=False)

    # 括弧がある行だけ除去処理
    df.loc[mask, column] = (
        df.loc[mask, column].astype(str).str.replace(r"\([^)]+\)", "", regex=True).str.strip()
    )

    # 全体をdatetimeに変換（括弧がない行も含め）
    df[column] = pd.to_datetime(df[column], format="%Y/%m/%d", errors="coerce")

    return df


def parse_str_column(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """
    欠損値はそのまま、文字列は strip() して object 型にする
    '<NA>' などの値も適切に処理する

    コードカラム（英語名が _cd で終わる）の場合は先頭ゼロを除去して正規化する
    例: "000123" → "123", "00123X" → "123X"
    """
    cleaned = df[col].copy()

    # '<NA>' などの特殊な値をNaNに変換
    cleaned = cleaned.replace(NA_STRING_VALUES, pd.NA)

    # 非欠損値だけに str.strip() を適用（NaN は触らない）
    cleaned = cleaned.where(cleaned.isna(), cleaned.astype(str).str.strip())

    # コードカラム（_cdで終わる）の場合は先頭ゼロを除去
    # 注意: この時点では日本語カラム名なので、英語名への変換前に適用する必要がある
    # そのため、カラム名ベースではなく、設定で判定する必要がある
    # 現時点では全てのstr型カラムに適用せず、後続の処理で対応する

    return df.assign(**{col: cleaned})


def normalize_code_column(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """
    コードカラムの先頭ゼロを除去して正規化する

    用途: 取引先CD、業者CD、品目CD、営業担当者CDなどのコードフィールド
    例: "000123" → "123", "00123X" → "123X", "0000" → "" (空文字列)

    :param df: 対象DataFrame
    :param col: 変換対象のカラム名
    :return: 変換後のDataFrame
    """
    cleaned = df[col].copy()

    # '<NA>' などの特殊な値をNaNに変換
    cleaned = cleaned.replace(NA_STRING_VALUES, pd.NA)

    # 非欠損値に対して先頭ゼロを除去
    # lstrip('0')を使用（例: "000123" → "123", "00123X" → "123X"）
    # 注意: "0000" のように全てゼロの場合は空文字列になるため、空文字列をNaNに変換
    cleaned = cleaned.where(cleaned.isna(), cleaned.astype(str).str.strip().str.lstrip("0"))

    # 空文字列をNaNに変換（全てゼロだった場合）
    cleaned = cleaned.replace("", pd.NA)

    return df.assign(**{col: cleaned})


def remove_commas_and_convert_numeric(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """
    カンマ付き数値文字列（例: '1,200'）を除去し、float型に変換する。
    '<NA>' や変換できない値は NaN として扱う。
    :param df: 対象DataFrame
    :param column: 変換対象のカラム名
    :return: 変換後のDataFrame
    """
    # カンマを除去し、特殊値や空文字をNaNに変換してからfloat変換
    cleaned = df[column].astype(str).str.replace(",", "")
    cleaned = cleaned.replace(NA_STRING_VALUES, pd.NA)
    df[column] = pd.to_numeric(cleaned, errors="coerce")
    return df


# 伝票日付カラムがDataFrameに存在するかチェックする関数
def has_denpyou_date_column(df: pd.DataFrame, column_name: str = "伝票日付") -> bool:
    """
    DataFrameに伝票日付カラムが存在するか判定
    :param df: チェック対象のDataFrame
    :param column_name: チェックするカラム名（デフォルト: 伝票日付）
    :return: 存在すればTrue、なければFalse
    """
    return column_name in df.columns


def clean_na_strings(val):
    """
    <NA>等の文字列や空文字列をNoneに変換する共通関数
    """
    if isinstance(val, str) and (
        val
        in [
            "<NA>",
            "NaN",
            "nan",
            "None",
            "NULL",
            "null",
            "#N/A",
            "#NA",
        ]
        or val.strip() == ""
    ):
        return None
    return val


def common_cleaning(df: pd.DataFrame) -> pd.DataFrame:
    """
    全カラム名と object 型の各値に対して、前後・内部のスペース（半角・全角）を除去。
    欠損値（NaN）には str() をかけないように注意。
    '<NA>' などの特殊な値も適切に処理する。
    """
    # カラム名の空白除去
    df.columns = [col.strip().replace(" ", "").replace("　", "") for col in df.columns]

    # 各object型カラムのスペース除去（NaNを保ったまま）
    for col in df.select_dtypes(include=["object"]).columns:
        cleaned = df[col].copy()

        # '<NA>' などの特殊な値をNaNに変換
        cleaned = cleaned.replace(NA_STRING_VALUES, pd.NA)

        cleaned = cleaned.where(
            cleaned.notna(),  # 非欠損値だけ変換を適用
            cleaned,  # 欠損値はそのまま
        )

        cleaned = cleaned.where(
            cleaned.isna(),  # 欠損値はそのまま
            cleaned.astype(str)
            .str.replace(" ", "", regex=False)
            .str.replace("　", "", regex=False)
            .str.strip(),
        )

        df[col] = cleaned

    return df
