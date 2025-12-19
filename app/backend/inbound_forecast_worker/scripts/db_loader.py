# -*- coding: utf-8 -*-
"""
db_loader.py - DB直接データ取得ユーティリティ

目的:
- train_daily_model.py, serve_predict_model_v4_2_4.py から使用
- CSV中間ファイルを廃止し、DBから直接DataFrameを取得
- 列名は学習側の想定（日本語）に合わせる

使用テーブル:
- 実績: stg.v_active_shogun_flash_receive (品目別、is_deleted=falseのみ)
- 予約: mart.v_reserve_daily_features (日次集計、customer_count含む)
"""
from __future__ import annotations

import os
from datetime import date
from typing import Optional

import pandas as pd


def load_raw_from_db(
    start_date: date,
    end_date: date,
    date_col: str = "伝票日付",
    item_col: str = "品名",
    weight_col: str = "正味重量",
    connection_string: Optional[str] = None,
) -> pd.DataFrame:
    """
    stg.v_active_shogun_flash_receive から品目別実績を取得（is_deleted=falseのみ）
    
    Args:
        start_date: 開始日（この日を含む）
        end_date: 終了日（この日を含む）
        date_col: 日付列名（デフォルト: 伝票日付）
        item_col: 品目列名（デフォルト: 品名）
        weight_col: 重量列名（デフォルト: 正味重量）
        connection_string: DB接続文字列（Noneの場合は環境変数から取得）
    
    Returns:
        DataFrame with columns: [date_col, item_col, weight_col]
        weight_col は kg 単位
        
    Raises:
        ValueError: 接続文字列が指定されていない
        RuntimeError: DB接続エラー
    
    Notes:
        - net_weight は kg 単位（変換なし）
        - v_active_* ビューは is_deleted=false でフィルタ済み
        - net_weight IS NOT NULL
        - item_name IS NOT NULL
    """
    import sqlalchemy
    from sqlalchemy import text
    
    # 接続文字列の取得
    if connection_string is None:
        connection_string = os.getenv("DATABASE_URL")
    
    if not connection_string:
        raise ValueError(
            "DB connection string not provided. "
            "Set --db-connection-string or DATABASE_URL environment variable."
        )
    
    # SQLクエリ（列名は一時的にプレースホルダー使用）
    sql = text("""
        SELECT 
            slip_date,
            item_name,
            net_weight AS weight_kg
        FROM stg.v_active_shogun_flash_receive
        WHERE slip_date >= :start_date 
          AND slip_date <= :end_date
          AND net_weight IS NOT NULL
          AND item_name IS NOT NULL
        ORDER BY slip_date, item_name
    """)
    
    try:
        engine = sqlalchemy.create_engine(connection_string)
        
        with engine.connect() as conn:
            result = conn.execute(sql, {
                "start_date": start_date,
                "end_date": end_date
            })
            rows = result.fetchall()
        
        # DataFrameに変換（英語列名）
        df = pd.DataFrame(rows, columns=["slip_date", "item_name", "weight_kg"])
        
        # 日付型変換
        df["slip_date"] = pd.to_datetime(df["slip_date"]).dt.normalize()
        
        # 重量をfloat型に変換（PostgreSQLのnumeric型はDecimalオブジェクトになるため）
        df["weight_kg"] = pd.to_numeric(df["weight_kg"], errors="coerce")
        
        # 列名を日本語にリネーム（学習側の想定に合わせる）
        df = df.rename(columns={
            "slip_date": date_col,
            "item_name": item_col,
            "weight_kg": weight_col,
        })
        
        return df
    
    except Exception as e:
        raise RuntimeError(
            f"Failed to load raw data from DB: {e}\n"
            f"Date range: {start_date} to {end_date}"
        ) from e


def load_reserve_from_db(
    start_date: date,
    end_date: date,
    date_col: str = "予約日",
    count_col: str = "台数",
    fixed_col: str = "固定客",
    connection_string: Optional[str] = None,
) -> pd.DataFrame:
    """
    mart.v_reserve_daily_features から予約データを取得
    
    Args:
        start_date: 開始日（この日を含む）
        end_date: 終了日（この日を含む）
        date_col: 日付列名（デフォルト: 予約日）
        count_col: 台数列名（デフォルト: 台数）
        fixed_col: 固定客列名（デフォルト: 固定客）
        connection_string: DB接続文字列（Noneの場合は環境変数から取得）
    
    Returns:
        DataFrame with columns: [date_col, count_col, fixed_col]
        
    Raises:
        ValueError: 接続文字列が指定されていない
        RuntimeError: DB接続エラー
    
    Notes:
        - データが無い日は含まれない（DBに行が存在する日のみ）
        - reserve_trucks, reserve_fixed_trucks は int型
    """
    import sqlalchemy
    from sqlalchemy import text
    
    # 接続文字列の取得
    if connection_string is None:
        connection_string = os.getenv("DATABASE_URL")
    
    if not connection_string:
        raise ValueError(
            "DB connection string not provided. "
            "Set --db-connection-string or DATABASE_URL environment variable."
        )
    
    # SQLクエリ（customer_count列を優先的に使用）
    sql = text("""
        SELECT 
            date,
            total_customer_count,
            fixed_customer_count,
            reserve_trucks,
            reserve_fixed_trucks
        FROM mart.v_reserve_daily_features
        WHERE date >= :start_date 
          AND date <= :end_date
        ORDER BY date
    """)
    
    try:
        engine = sqlalchemy.create_engine(connection_string)
        
        with engine.connect() as conn:
            result = conn.execute(sql, {
                "start_date": start_date,
                "end_date": end_date
            })
            rows = result.fetchall()
        
        # DataFrameに変換（英語列名）
        df = pd.DataFrame(rows, columns=[
            "date", "total_customer_count", "fixed_customer_count",
            "reserve_trucks", "reserve_fixed_trucks"
        ])
        
        # 日付型変換
        df["date"] = pd.to_datetime(df["date"]).dt.normalize()
        
        # 数値列を明示的に数値型に変換
        df["total_customer_count"] = pd.to_numeric(df["total_customer_count"], errors="coerce")
        df["fixed_customer_count"] = pd.to_numeric(df["fixed_customer_count"], errors="coerce")
        df["reserve_trucks"] = pd.to_numeric(df["reserve_trucks"], errors="coerce")
        df["reserve_fixed_trucks"] = pd.to_numeric(df["reserve_fixed_trucks"], errors="coerce")
        
        # 列名を日本語にリネーム（学習側の想定に合わせる）
        # count_col: 企業数（total_customer_count）を使用
        # fixed_col: 固定客企業数（fixed_customer_count）をbool化して使用
        df = df.rename(columns={
            "date": date_col,
            "total_customer_count": count_col,
            "fixed_customer_count": fixed_col,
        })
        
        # 不要な列を削除（reserve_trucks, reserve_fixed_trucksは使わない）
        df = df[[date_col, count_col, fixed_col]]
        
        return df
    
    except Exception as e:
        raise RuntimeError(
            f"Failed to load reserve data from DB: {e}\n"
            f"Date range: {start_date} to {end_date}"
        ) from e


if __name__ == "__main__":
    # テスト用
    import sys
    from datetime import timedelta
    
    # 接続文字列をコマンドライン引数から取得
    if len(sys.argv) < 2:
        print("Usage: python db_loader.py <connection_string>")
        sys.exit(1)
    
    conn_str = sys.argv[1]
    
    # テストデータ取得
    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=30)
    
    print(f"Testing load_raw_from_db({start}, {end})...")
    raw_df = load_raw_from_db(start, end, connection_string=conn_str)
    print(f"✅ Loaded {len(raw_df)} raw records")
    print(f"Columns: {raw_df.columns.tolist()}")
    print(f"Date range: {raw_df['伝票日付'].min()} to {raw_df['伝票日付'].max()}")
    print(f"Sample:\n{raw_df.head()}\n")
    
    print(f"Testing load_reserve_from_db({start}, {end})...")
    reserve_df = load_reserve_from_db(start, end, connection_string=conn_str)
    print(f"✅ Loaded {len(reserve_df)} reserve records")
    print(f"Columns: {reserve_df.columns.tolist()}")
    print(f"Date range: {reserve_df['予約日'].min()} to {reserve_df['予約日'].max()}")
    print(f"Sample:\n{reserve_df.head()}\n")
