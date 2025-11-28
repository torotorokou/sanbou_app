import re
import pandas as pd
from typing import Optional, Dict, List


def make_cell_num(master_csv: pd.DataFrame) -> pd.DataFrame:
    start_cells = {"有価": "C15", "処分": "C23", "ヤード": "C33"}
    col_list = ["C", "F", "I", "L", "O"]
    return make_cell_num_cal(master_csv, start_cells=start_cells, col_list=col_list)


def make_cell_num_cal(
    master_csv: pd.DataFrame,
    start_cells: Dict[str, str],
    col_list: Optional[List[str]] = None,
    category_col: str = "カテゴリ",
) -> pd.DataFrame:
    if col_list is None:
        col_list = ["C", "F", "I", "L", "O"]

    df_target = (
        master_csv[
            (master_csv["セルロック"] == 1)
            | ((master_csv["セルロック"] != 1) & (master_csv["値"] != 0))
        ]
        .copy()
        .sort_values("順番")
    )

    df_target["セル"] = ""

    for category, group in df_target.groupby(category_col):
        cat_key = str(category)
        start_cell = start_cells.get(cat_key)
        if not start_cell:
            raise ValueError(f"[カテゴリ: {category}] に対する開始セルが指定されていません。")

        match = re.match(r"([A-Z]+)(\d+)", start_cell)
        if not match:
            raise ValueError(
                f"[カテゴリ: {category}] の開始セル '{start_cell}' は 'C14' の形式である必要があります。"
            )

        base_row = int(match[2])
        row_step = 2

        for i, df_idx in enumerate(group.index):
            col = col_list[i % len(col_list)]
            row = base_row + (i // len(col_list)) * row_step
            df_target.at[df_idx, "セル"] = f"{col}{row}"

    return df_target
