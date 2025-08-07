import streamlit as st
import pandas as pd
import logging
from app.api.st_app.utils.config_loader import clean_na_strings

# ロガーの設定
logger = logging.getLogger(__name__)


def confirm_transport_selection(df_after: pd.DataFrame) -> None:
    """運搬業者の選択内容を確認するダイアログを表示する

    処理の流れ:
        1. 選択された運搬業者の一覧を表示
        2. 確認用のYes/Noボタンを表示
        3. ユーザーの選択に応じて処理を分岐
            - Yes: 次のステップへ進む（process_mini_step = 2）
            - No: Step1（選択画面）に戻る（process_mini_step = 1）

    Args:
        df_after (pd.DataFrame): 運搬業者が選択された出荷データ
    """
    # セッション状態の初期化
    if "transport_selection_confirmed" not in st.session_state:
        st.session_state.transport_selection_confirmed = False

    def _create_confirmation_view(df: pd.DataFrame) -> pd.DataFrame:
        """確認用の表示データを作成"""
        filtered_df = df[df["運搬業者"].notna()]
        return filtered_df[["業者名", "品名", "明細備考", "運搬業者"]]

    def _show_confirmation_buttons() -> tuple[bool, bool]:
        """確認用のYes/Noボタンを表示"""
        st.write("この運搬業者選択で確定しますか？")
        col1, col2 = st.columns([1, 1])

        with col1:
            yes_clicked = st.button("✅ はい（この内容で確定）", key="yes_button")
        with col2:
            no_clicked = st.button("🔁 いいえ（やり直す）", key="no_button")

        return yes_clicked, no_clicked

    def _handle_user_selection(yes_clicked: bool, no_clicked: bool) -> None:
        """ユーザーの選択結果を処理"""
        if yes_clicked:
            st.success("✅ 確定されました。次に進みます。")
            st.session_state.transport_selection_confirmed = True
            st.session_state.process_mini_step = 2
            st.rerun()

        if no_clicked:
            st.warning("🔁 選択をやり直します（Step1に戻ります）")
            st.session_state.transport_selection_confirmed = False
            st.session_state.process_mini_step = 1
            st.rerun()

    # すでに確認済みの場合はスキップ
    if st.session_state.transport_selection_confirmed:
        return

    # メイン処理の実行
    st.title("運搬業者の確認")

    # 1. 確認用データの表示
    df_view = _create_confirmation_view(df_after)
    st.dataframe(df_view)

    # 2. 確認ボタンの表示と選択結果の取得
    yes_clicked, no_clicked = _show_confirmation_buttons()

    # 3. 選択結果の処理
    _handle_user_selection(yes_clicked, no_clicked)

    # 4. ユーザーの操作待ち
    st.stop()


def apply_column_addition_by_keys(
    base_df: pd.DataFrame,
    addition_df: pd.DataFrame,
    join_keys: list,
    value_col_to_add: str,
    update_target_col: str,
) -> pd.DataFrame:
    """指定されたキーで結合し、値を加算する関数"""
    # データをクリーンアップ
    addition_df = addition_df.copy()
    if value_col_to_add in addition_df.columns:
        addition_df[value_col_to_add] = addition_df[value_col_to_add].apply(
            clean_na_strings
        )
        addition_df[value_col_to_add] = pd.to_numeric(
            addition_df[value_col_to_add], errors="coerce"
        )

    # 結合処理
    result_df = base_df.merge(
        addition_df[join_keys + [value_col_to_add]], on=join_keys, how="left"
    )

    # 値の加算
    if update_target_col in result_df.columns:
        result_df[update_target_col] = result_df[update_target_col].fillna(
            0
        ) + result_df[value_col_to_add].fillna(0)
    else:
        result_df[update_target_col] = result_df[value_col_to_add].fillna(0)

    # 不要な列を削除
    if value_col_to_add != update_target_col and value_col_to_add in result_df.columns:
        result_df = result_df.drop(columns=[value_col_to_add])

    return result_df


def apply_transport_fee_by_vendor(
    df_after: pd.DataFrame, df_transport: pd.DataFrame
) -> pd.DataFrame:
    """運搬業者ごとの運搬費を適用する関数

    Args:
        df_after: 処理対象の出荷データフレーム
        df_transport: 運搬費データフレーム

    Returns:
        pd.DataFrame: 運搬費が適用された出荷データフレーム
    """
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
    df_after: pd.DataFrame, df_transport: pd.DataFrame
) -> pd.DataFrame:
    """重量に基づく運搬費を計算して適用する関数

    Args:
        df_after: 処理対象の出荷データフレーム
        df_transport: 運搬費データフレーム（"数字*weight"形式の運搬費を含む）

    Returns:
        pd.DataFrame: 重量に基づく運搬費が適用された出荷データフレーム
    """
    # 重量ベースの運搬費行を抽出
    transport_fee_col = (
        df_transport["運搬費"].astype(str).str.replace(r"\s+", "", regex=True)
    )
    weight_based_mask = transport_fee_col.str.fullmatch(r"\d+\*weight", na=False)
    weight_based_transport = df_transport[weight_based_mask].copy()

    # 運搬費係数の抽出と変換
    weight_based_transport["運搬費係数"] = (
        weight_based_transport["運搬費"].str.extract(r"^(\d+)")[0].astype(float)
    )

    # 必要な列の選択と重複除去
    weight_based_transport = weight_based_transport.drop_duplicates(
        subset=["業者CD", "運搬業者"]
    )[["業者CD", "運搬業者", "運搬費係数"]]

    # 運搬費係数の適用
    df_result = df_after.merge(
        weight_based_transport,
        how="left",
        on=["業者CD", "運搬業者"],
        suffixes=("", "_formula"),
    )

    # 重量ベースの運搬費計算
    has_coefficient_mask = df_result["運搬費係数"].notna()
    df_result.loc[has_coefficient_mask, "運搬費"] = (
        df_result.loc[has_coefficient_mask, "運搬費係数"]
        * df_result.loc[has_coefficient_mask, "正味重量"]
    ).astype(float)

    return df_result


def make_total_sum(df, master_csv):
    """ブロック単価の計算を行う関数"""

    # 個々の金額計算と計算用重量の設定
    def calculate_row(row):
        if row["単位名"] == "kg":
            row["金額"] = row["単価"] * row["正味重量"]
        elif row["単位名"] == "台":
            row["金額"] = row["単価"] * row["数量"]
        return row

    # 行ごとに計算を適用
    df = df.apply(calculate_row, axis=1)

    # 総額の計算
    df["総額"] = df["金額"] + df["運搬費"]

    # ブロック単価の計算（計算用重量を使用）
    df["ブロック単価"] = (df["総額"] / df["正味重量"].replace(0, pd.NA)).round(2)

    return df


def df_cul_filtering(df):
    """表示用データのフィルタリングを行う関数"""

    # dfカラムのフィルタリング
    df = df[["業者名", "明細備考", "正味重量", "総額", "ブロック単価"]]

    return df


def first_cell_in_template(df):
    """テンプレートの最初のセルを作成する関数"""
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

    for idx, row in df.iterrows():
        for col, col_letter in full_col_to_cell.items():
            cell = f"{col_letter}{start_row + idx}"
            value = row[col]
            full_cell_info.append({"大項目": col, "セル": cell, "値": value})

    full_cell_df = pd.DataFrame(full_cell_info)

    return full_cell_df


def make_sum_date(df, df_shipping):
    """日付集計を追加する関数"""
    try:
        # 日付ユーティリティのインポートを試行
        try:
            from app.api.st_app.utils.date_tools import to_reiwa_format
        except ImportError:
            # インポートに失敗した場合のフォールバック
            def to_reiwa_format(date_str):
                return "令和6年8月6日"  # 仮の実装

        # 日付を令和表記に変換（例: "令和6年5月16日"）
        date = to_reiwa_format(df_shipping["伝票日付"].iloc[0])

        # 追加行を定義
        new_row = pd.DataFrame([{"大項目": "日付", "セル": "E4", "値": date}])

        # df に行を追加
        df = pd.concat([df, new_row], ignore_index=True)

        return df
    except Exception as e:
        logger.error(f"日付集計中にエラーが発生しました: {e}")
        return df
