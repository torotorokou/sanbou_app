from app.infra.report_utils.formatters import set_value_fast_safe


def reflect_total_from_factory(master_csv, df_factory):
    """工場日報の総合計（搬出量）をバランスシートのマスターへ反映する。"""
    total_sum = df_factory.loc[df_factory["大項目"] == "総合計", "値"].squeeze()

    match_columns = ["大項目"]
    match_value = ["搬出量"]
    master_csv = set_value_fast_safe(master_csv, match_columns, match_value, total_sum)

    return master_csv


def process_factory_report(dfs, master_csv):
    """services 側の factory_report 処理結果を反映して master_csv を返す。"""
    from app.application.usecases.reports.factory_report import (
        process as _process_factory_report,
    )

    df_factory = _process_factory_report(dfs)
    after_master_csv = reflect_total_from_factory(master_csv, df_factory)
    return after_master_csv
