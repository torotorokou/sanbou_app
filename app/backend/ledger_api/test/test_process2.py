import pandas as pd
from app.st_app.logic.manage.processors.block_unit_price import process2


def test_make_total_sum_basic():
    df = pd.DataFrame(
        [
            {"単位名": "kg", "単価": 100, "正味重量": 2, "運搬費": 50},
            {"単位名": "台", "単価": 200, "数量": 3, "運搬費": 0},
        ]
    )
    res = process2.make_total_sum(df, pd.DataFrame())
    assert "金額" in res.columns
    assert res.loc[0, "金額"] == 200
    assert res.loc[1, "金額"] == 600
    assert "総額" in res.columns
    assert res.loc[0, "総額"] == 250


def test_df_cul_filtering_columns():
    df = pd.DataFrame(
        [{"業者名": "A", "明細備考": "x", "正味重量": 10, "総額": 1000, "ブロック単価": 100}]
    )
    out = process2.df_cul_filtering(df)
    assert list(out.columns) == ["業者名", "明細備考", "正味重量", "総額", "ブロック単価"]


def test_first_cell_in_template_structure():
    df = pd.DataFrame(
        [{"業者名": "A", "明細備考": "x", "正味重量": 10, "総額": 1000, "ブロック単価": 100}]
    )
    out = process2.first_cell_in_template(df)
    # 5 columns * 1 row -> 5 entries
    assert len(out) == 5
    assert set(out.columns) == {"大項目", "セル", "値"}


def test_make_sum_date_appends():
    master = pd.DataFrame([{"大項目": "foo", "セル": "A1", "値": "v"}])
    df_shipping = pd.DataFrame([{"伝票日付": "2025-05-16"}])
    out = process2.make_sum_date(master, df_shipping)
    # Expect the new row with 大項目 日付
    assert any(out["大項目"] == "日付")
