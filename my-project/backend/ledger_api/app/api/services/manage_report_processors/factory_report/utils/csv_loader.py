import pandas as pd
from typing import Dict, List, Union, Any
from app.api.services.manage_report_processors.factory_report.utils.config_loader import (
    get_required_columns_definition,
)
from app.api.services.manage_report_processors.factory_report.utils.logger import (
    app_logger,
)


def load_filtered_dataframe(
    dfs: Dict[str, pd.DataFrame],
    key: str,
    target_columns: Union[List[str], Dict[str, str]],
) -> pd.DataFrame:
    """
    指定された辞書型DataFrameから、対象キーのDataFrameを取得し、
    指定されたカラムのみを抽出して返す。

    Parameters:
        dfs (dict): 複数のDataFrameを格納した辞書。例: {"receive": df1, "yard": df2}
        key (str): 対象となるDataFrameのキー名。例: "receive"
        target_columns (list or dict): 抽出するカラム名のリスト or {カラム名: 型}

    Returns:
        pd.DataFrame: 指定されたカラムのみを持つDataFrame（フィルタ済み）
    """
    logger = app_logger()

    if key not in dfs:
        raise KeyError(f"{key} はdfsに存在しません。利用可能なキー: {list(dfs.keys())}")

    df = dfs[key]

    # --- 型付き辞書だったらキーだけを使う
    if isinstance(target_columns, dict):
        target_columns = list(target_columns.keys())

    # --- listの中身がさらにlistなら flatten（[[...]] → [...]）
    if (
        isinstance(target_columns, list)
        and target_columns
        and isinstance(target_columns[0], list)
    ):
        target_columns = target_columns[0]

    # カラムの存在チェック
    missing_cols = [col for col in target_columns if col not in df.columns]
    if missing_cols:
        logger.error(f"{key} に必要なカラムが不足しています: {missing_cols}")
        logger.error(f"利用可能なカラム: {list(df.columns)}")
        raise ValueError(f"{key} に次のカラムが存在しません: {missing_cols}")

    return df[target_columns].copy()


def flatten_list(nested_list: List[Any]) -> List[Any]:
    """
    1段ネストされたリストをフラットにする。
    例: [['A', 'B'], 'C'] → ['A', 'B', 'C']

    Parameters:
        nested_list (list): ネストされたリスト

    Returns:
        list: フラット化されたリスト
    """
    flat = []
    for item in nested_list:
        if isinstance(item, list):
            flat.extend(item)
        else:
            flat.append(item)
    return flat


def load_all_filtered_dataframes(
    dfs: Dict[str, pd.DataFrame],
    keys: List[str],
    template_name: str,
) -> Dict[str, pd.DataFrame]:
    """
    指定された帳票テンプレートとCSVキーに基づき、必要なカラムのみ抽出して返す。

    Parameters:
        dfs (dict): 入力データフレーム辞書
        keys (list): 処理対象のキーリスト
        template_name (str): テンプレート名

    Returns:
        dict: フィルタリング済みデータフレーム辞書
    """
    logger = app_logger()
    df_dict = {}

    try:
        column_defs = get_required_columns_definition()
        template_columns = column_defs.get(template_name, {})
        logger.info(
            f"🔍 対象テンプレート: {template_name}, カラム定義: {template_columns}"
        )
    except Exception as e:
        logger.warning(f"カラム定義の取得に失敗しました: {e}")
        # フォールバック: 全てのカラムを使用
        template_columns = {}

    for key in keys:
        if key in dfs:
            target_columns = template_columns.get(key, [])
            # ネストされている場合に備えて flatten
            if target_columns:
                target_columns = flatten_list(target_columns)
                df_dict[key] = load_filtered_dataframe(dfs, key, target_columns)
            else:
                # カラム定義がない場合は全カラムを使用
                logger.warning(
                    f"カラム定義が見つからないため、全カラムを使用します: {key}"
                )
                df_dict[key] = dfs[key].copy()
        else:
            logger.warning(f"キー '{key}' がdfsに存在しません。スキップします。")

    return df_dict
