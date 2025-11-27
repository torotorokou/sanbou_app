import pandas as pd

from app.api.services.report.ledger.factory_report import process as proc_factory
from app.api.services.report.ledger.average_sheet import process as proc_average
from app.api.services.report.ledger.management_sheet import process as proc_management


def test_factory_report_with_empty_inputs():
    dfs = {"shipment": pd.DataFrame(), "yard": pd.DataFrame()}
    df = proc_factory(dfs)
    assert isinstance(df, pd.DataFrame)


def test_average_sheet_with_minimal_receive():
    dfs = {
        "receive": pd.DataFrame(
            {
                "伝票区分名": ["売上"],
                "単位名": ["kg"],
                "集計項目CD": [1],
                "品名CD": [1],
                "正味重量": [100],
                "金額": [1000],
                "受入番号": ["A1"],
                "伝票日付": [pd.Timestamp("2025-10-01")],
            }
        )
    }
    df = proc_average(dfs)
    assert isinstance(df, pd.DataFrame)
    assert "値" in df.columns
    # 日付/曜日等の文字列書き込みがあっても DataFrame が生成されること
    assert df["値"].dtype is not None


def test_management_sheet_with_minimal_receive():
    dfs = {
        "receive": pd.DataFrame(
            {"伝票日付": [pd.Timestamp("2025-10-01")]}
        )
    }
    df = proc_management(dfs)
    assert isinstance(df, pd.DataFrame)
    assert "値" in df.columns