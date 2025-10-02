from app.api.services.report.ledger.utils.excel_tools import (
    add_label_rows,
)


def make_label(df):
    # 有価ラベル
    final_df = add_label_rows(df, label_source_col="大項目", offset=-1)
    return final_df
