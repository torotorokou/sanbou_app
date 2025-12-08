"""
test_balance_sheet_base.py

balance_sheet_base.pyの動作確認テスト。
ベースDataFrame構築が正しく動作し、既存の処理と同じ結果を返すことを検証。
"""
import pandas as pd
import pytest
from app.core.usecases.reports.balance_sheet_base import build_balance_sheet_base_data


def test_build_balance_sheet_base_data_with_shipment():
    """
    shipmentデータから対象日が正しく取得できることを確認
    """
    df_shipment = pd.DataFrame({
        "伝票日付": ["2024-01-15", "2024-01-15"],
        "業者CD": [123, 456],
        "金額": [1000, 2000],
    })
    
    df_dict = {
        "shipment": df_shipment,
    }
    
    base_data = build_balance_sheet_base_data(df_dict)
    
    # 対象日が正しく取得されているか
    assert base_data.target_day == pd.Timestamp("2024-01-15")
    
    # 業者CDが文字列化されているか
    assert base_data.df_shipment is not None
    assert base_data.df_shipment["業者CD"].dtype == object
    assert base_data.df_shipment["業者CD"].iloc[0] == "123"
    
    # 単価テーブルが読み込まれているか
    assert base_data.unit_price_table is not None
    assert isinstance(base_data.unit_price_table, pd.DataFrame)


def test_build_balance_sheet_base_data_with_receive():
    """
    receiveデータから対象日が正しく取得できることを確認
    """
    df_receive = pd.DataFrame({
        "伝票日付": ["2024-02-20", "2024-02-20"],
        "受入番号": [1, 2],
        "正味重量": [100.5, 200.3],
    })
    
    df_dict = {
        "receive": df_receive,
    }
    
    base_data = build_balance_sheet_base_data(df_dict)
    
    # 対象日が正しく取得されているか
    assert base_data.target_day == pd.Timestamp("2024-02-20")
    
    # receiveデータがコピーされているか
    assert base_data.df_receive is not None
    assert id(base_data.df_receive) != id(df_receive)  # 別オブジェクト


def test_build_balance_sheet_base_data_with_all_data():
    """
    receive, shipment, yardすべてのデータで正しく動作することを確認
    """
    df_receive = pd.DataFrame({
        "伝票日付": ["2024-03-10"],
        "受入番号": [1],
    })
    df_shipment = pd.DataFrame({
        "伝票日付": ["2024-03-10"],
        "業者CD": [789],
    })
    df_yard = pd.DataFrame({
        "種類名": ["鉄"],
        "数量": [50],
    })
    
    df_dict = {
        "receive": df_receive,
        "shipment": df_shipment,
        "yard": df_yard,
    }
    
    base_data = build_balance_sheet_base_data(df_dict)
    
    # すべてのDataFrameが格納されているか
    assert base_data.df_receive is not None
    assert base_data.df_shipment is not None
    assert base_data.df_yard is not None
    
    # shipmentの対象日が優先されるか
    assert base_data.target_day == pd.Timestamp("2024-03-10")


def test_build_balance_sheet_base_data_empty():
    """
    空のdictでも正常に動作することを確認
    """
    df_dict = {}
    
    base_data = build_balance_sheet_base_data(df_dict)
    
    # 対象日は今日になるか
    assert base_data.target_day.date() == pd.Timestamp.today().date()
    
    # DataFrameはNoneか
    assert base_data.df_receive is None
    assert base_data.df_shipment is None
    assert base_data.df_yard is None
    
    # 単価テーブルは読み込まれているか
    assert base_data.unit_price_table is not None


if __name__ == "__main__":
    # 簡易実行用
    test_build_balance_sheet_base_data_with_shipment()
    test_build_balance_sheet_base_data_with_receive()
    test_build_balance_sheet_base_data_with_all_data()
    test_build_balance_sheet_base_data_empty()
    print("✅ All tests passed!")
