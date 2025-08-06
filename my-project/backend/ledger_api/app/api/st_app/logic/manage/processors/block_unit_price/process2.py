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
    """重量ベースの運搬費を適用する関数

    Args:
        df_after: 処理対象の出荷データフレーム
        df_transport: 運搬費データフレーム

    Returns:
        pd.DataFrame: 重量ベースの運搬費が適用された出荷データフレーム
    """
    # 重量列の数値化とクリーンアップ
    if "重量" in df_after.columns:
        df_after["重量"] = df_after["重量"].apply(clean_na_strings)
        df_after["重量"] = pd.to_numeric(df_after["重量"], errors="coerce").fillna(0)

    if "重量単価" in df_transport.columns:
        df_transport["重量単価"] = df_transport["重量単価"].apply(clean_na_strings)
        df_transport["重量単価"] = pd.to_numeric(
            df_transport["重量単価"], errors="coerce"
        ).fillna(0)

    # 重量ベースの運搬費計算
    result_df = df_after.merge(
        df_transport[["運搬業者", "重量単価"]], on="運搬業者", how="left"
    )

    # 運搬費 = 重量 × 重量単価
    result_df["運搬費"] = result_df["重量"].fillna(0) * result_df["重量単価"].fillna(0)

    # 不要な列を削除
    if "重量単価" in result_df.columns:
        result_df = result_df.drop(columns=["重量単価"])

    return result_df


def process_transport_costs(df_after: pd.DataFrame) -> pd.DataFrame:
    """運搬費の総合処理を行う関数

    Args:
        df_after: 処理対象の出荷データフレーム

    Returns:
        pd.DataFrame: 運搬費が処理された出荷データフレーム
    """
    try:
        # 運搬費マスタの読み込み（モックデータ）
        df_transport = pd.DataFrame(
            {
                "業者CD": ["001", "002", "003"],
                "運搬業者": ["運搬A", "運搬B", "運搬C"],
                "運搬費": [1000, 1500, 2000],
                "重量単価": [100, 150, 200],
            }
        )

        if df_transport is None or df_transport.empty:
            logger.warning("運搬費データが空です")
            return df_after

        # 運搬費の適用
        if "運搬業者" in df_after.columns:
            # 業者ベースの運搬費適用
            df_after = apply_transport_fee_by_vendor(df_after, df_transport)

            # 重量ベースの運搬費適用（必要に応じて）
            if "重量" in df_after.columns and "重量単価" in df_transport.columns:
                df_after = apply_weight_based_transport_fee(df_after, df_transport)

        return df_after

    except Exception as e:
        logger.error(f"運搬費処理中にエラーが発生しました: {e}")
        return df_after


def main_process(df_after: pd.DataFrame) -> pd.DataFrame:
    """メイン処理関数

    Args:
        df_after: 処理対象の出荷データフレーム

    Returns:
        pd.DataFrame: 処理済みの出荷データフレーム
    """
    try:
        # 運搬費処理
        df_after = process_transport_costs(df_after)

        # その他の処理をここに追加

        return df_after

    except Exception as e:
        logger.error(f"メイン処理中にエラーが発生しました: {e}")
        return df_after
