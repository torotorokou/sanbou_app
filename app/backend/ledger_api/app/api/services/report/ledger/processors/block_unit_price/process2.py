import pandas as pd
from pandas import DataFrame


def apply_transport_fee_by_vendor(
    df_after: DataFrame, df_transport: DataFrame
) -> DataFrame:
    """運搬業者ごとの運搬費を適用する関数

    Args:
        df_after: 処理対象の出荷データフレーム
        df_transport: 運搬費データフレーム

    Returns:
        pd.DataFrame: 運搬費が適用された出荷データフレーム
    """
    from app.api.services.report.ledger.utils.column_utils import apply_column_addition_by_keys

    # 運搬業者が設定されている行を抽出
    target_rows = df_after[df_after["運搬業者"].notna()].copy()

    # 運搬費の適用（業者CDで結合）
    updated_target_rows = apply_column_addition_by_keys(
        base_df=target_rows,
        addition_df=df_transport,
        join_keys=["業者CD", "運搬業者"],
        value_col_to_add="運搬費",
        update_target_col="運搬費",
    )

    # 運搬業者が未設定の行を保持
    non_transport_rows = df_after[df_after["運搬業者"].isna()].copy()

    # 処理済みデータの結合
    df_after = pd.concat([updated_target_rows, non_transport_rows], ignore_index=True)

    return df_after


def apply_weight_based_transport_fee(
    df_after: DataFrame, df_transport: DataFrame
) -> DataFrame:
    """運搬費係数を用いて重量ベースの運搬費を再計算する"""

    out = df_after.copy()

    fee_str = df_transport.get("運搬費", pd.Series(dtype=object)).astype(str).str.replace(
        r"\s+", "", regex=True
    )
    mask = fee_str.str.fullmatch(r"\d+\*weight", na=False)
    t = df_transport[mask].copy()

    if not t.empty:
        t["運搬費係数"] = t["運搬費"].str.extract(r"^(\d+)")[0].astype(float)
        t = t.drop_duplicates(subset=["業者CD", "運搬業者"])[
            ["業者CD", "運搬業者", "運搬費係数"]
        ]

        out = out.merge(t, on=["業者CD", "運搬業者"], how="left", suffixes=("", "_formula"))

        has_coef = out["運搬費係数"].notna()
        weight = pd.to_numeric(
            out.get("正味重量", pd.Series(dtype="float64")), errors="coerce"
        )
        coef = pd.to_numeric(
            out.get("運搬費係数", pd.Series(dtype="float64")), errors="coerce"
        )
        out.loc[has_coef, "運搬費"] = (coef[has_coef] * weight[has_coef]).astype(float)

    return out


def make_total_sum(df: DataFrame, master_csv: DataFrame) -> DataFrame:
    # 個々の金額計算と計算用重量の設定
    def calculate_row(row):
        if row["単位名"] == "kg":
            row["金額"] = row["単価"] * row["正味重量"]
        elif row["単位名"] == "台":
            row["金額"] = row["単価"] * row["数量"]
        return row

    # 行ごとに計算を適用
    # apply returns a Series per row; assign back to DataFrame to satisfy typing
    df = df.apply(calculate_row, axis=1)  # type: ignore[assignment]

    # 総額の計算
    df["総額"] = df["金額"] + df["運搬費"]

    # ブロック単価の計算（計算用重量を使用）
    df["ブロック単価"] = (df["総額"] / df["正味重量"].replace(0, pd.NA)).round(2)

    return df


def df_cul_filtering(df: DataFrame) -> DataFrame:

    # dfカラムのフィルタリング
    df = df[["業者名", "明細備考", "正味重量", "総額", "ブロック単価"]]

    #     # カラム名の変更
    #     df = df.rename(columns={
    #     # "業者名": "取引先名",
    #     "明細備考": "明細備考",
    #     "正味重量": "数量",
    #     "総額": "金額",
    #     "ブロック単価": "単価"
    # })
    return df


def first_cell_in_template(df: DataFrame) -> DataFrame:

    start_row = 7
    full_col_to_cell = {
        "業者名": "B",
        "明細備考": "C",
        "正味重量": "D",
        "総額": "E",
        "ブロック単価": "F",
    }

    # セル情報を再構築
    full_cell_info = []

    for i, (_, row) in enumerate(df.iterrows()):
        for col, col_letter in full_col_to_cell.items():
            cell = f"{col_letter}{start_row + i}"
            value = row[col]
            full_cell_info.append({"大項目": col, "セル": cell, "値": value})

    full_cell_df = pd.DataFrame(full_cell_info)

    return full_cell_df


def make_sum_date(df: DataFrame, df_shipping: DataFrame) -> DataFrame:
    from app.api.services.report.ledger.utils.date_tools import to_reiwa_format

    # 日付を令和表記に変換（例: "令和6年5月16日"）
    date = to_reiwa_format(df_shipping["伝票日付"].iloc[0])

    # 追加行を定義
    new_row = pd.DataFrame([{"大項目": "日付", "セル": "E4", "値": date}])

    # df に行を追加
    df = pd.concat([df, new_row], ignore_index=True)

    return df


def calculate_block_unit_price(df: DataFrame) -> DataFrame:
    """ブロック単価を計算する関数

    Args:
        df: 処理対象のデータフレーム

    Returns:
        pd.DataFrame: ブロック単価が計算されたデータフレーム
    """
    # 総額の計算（単価 × 正味重量 + 運搬費）
    df["総額"] = df["単価"] * df["正味重量"] + df["運搬費"]

    # ブロック単価の計算（総額 ÷ 正味重量）、0除算を回避
    df["ブロック単価"] = (df["総額"] / df["正味重量"].replace(0, pd.NA)).round(2)
    return df


def filter_display_columns(df: DataFrame) -> DataFrame:
    """表示用の列を選択する関数

    Args:
        df: 処理対象のデータフレーム

    Returns:
        pd.DataFrame: 表示用に列が選択されたデータフレーム
    """
    display_columns = ["業者名", "明細備考", "正味重量", "総額", "ブロック単価"]
    return df[display_columns]


def create_cell_mapping(df: DataFrame) -> DataFrame:
    """データフレームの値をExcelセルにマッピングする関数

    Args:
        df: 処理対象のデータフレーム

    Returns:
        pd.DataFrame: セルマッピング情報を含むデータフレーム
    """
    start_row = 7
    column_to_cell = {
        "業者名": "B",
        "明細備考": "C",
        "正味重量": "D",
        "総額": "E",
        "ブロック単価": "F",
    }

    # セルマッピング情報の作成
    cell_mappings = []
    for i, (_, row) in enumerate(df.iterrows()):
        for column, cell_letter in column_to_cell.items():
            cell_position = f"{cell_letter}{start_row + i}"
            cell_mappings.append(
                {"大項目": column, "セル": cell_position, "値": row[column]}
            )

    return pd.DataFrame(cell_mappings)


def add_date_information(df: DataFrame, df_shipping: DataFrame) -> DataFrame:
    """日付情報を追加する関数

    Args:
        df: セルマッピング情報を含むデータフレーム
        df_shipping: 出荷データフレーム

    Returns:
        pd.DataFrame: 日付情報が追加されたデータフレーム
    """
    from app.api.services.report.ledger.utils.date_tools import to_reiwa_format

    # 伝票日付を令和形式に変換
    reiwa_date = to_reiwa_format(df_shipping["伝票日付"].iloc[0])

    # 日付情報の追加
    date_row = pd.DataFrame([{"大項目": "日付", "セル": "E4", "値": reiwa_date}])

    return pd.concat([df, date_row], ignore_index=True)
