# -*- coding: utf-8 -*-
"""
db_extract.py - 実験用DBデータ抽出ユーティリティ

目的:
- lookback期間別実験のために、DBから指定期間のデータを抽出
- train_daily_model.pyが読める形式（日本語列名）でCSV化
- リーク防止: 実績は end_date-1まで、予約は end_date当日まで

使用テーブル:
- 実績: stg.v_active_shogun_flash_receive (品目別、is_deleted=falseのみ)
- 予約: mart.v_reserve_daily_features (日次集計、customer_count含む)
"""
from __future__ import annotations

import os
import logging
from datetime import date, timedelta
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    """抽出結果"""
    raw_csv_path: Path
    reserve_csv_path: Path
    raw_record_count: int
    raw_date_min: date
    raw_date_max: date
    raw_unique_days: int
    reserve_record_count: int
    reserve_date_min: Optional[date]
    reserve_date_max: Optional[date]
    avg_weight_kg: float


def extract_experiment_data(
    end_date: date,
    lookback_days: int,
    output_dir: Path,
    connection_string: Optional[str] = None,
    include_eval_reserve: bool = True,
) -> ExtractionResult:
    """
    実験用にDBからデータを抽出し、CSV形式で保存する。
    
    Args:
        end_date: 評価基準日（この日を予測対象とする）
        lookback_days: 学習に使う過去日数
        output_dir: 出力ディレクトリ
        connection_string: DB接続文字列（Noneの場合は環境変数から取得）
        include_eval_reserve: end_date当日の予約を含めるか
    
    Returns:
        ExtractionResult: 抽出結果（パス、件数など）
    
    抽出条件:
        - 実績: [end_date - lookback_days] 〜 [end_date - 1]（リーク防止）
        - 予約: [end_date - lookback_days] 〜 [end_date]（当日予約は特徴量として使用OK）
    """
    import sqlalchemy
    from sqlalchemy import text
    
    # 接続文字列の取得
    if connection_string is None:
        connection_string = os.getenv("DATABASE_URL")
    
    if not connection_string:
        raise ValueError(
            "DB connection string not provided. "
            "Set connection_string or DATABASE_URL environment variable."
        )
    
    # 日付範囲計算
    # 実績: end_date-1までしか使わない（リーク防止）
    raw_start_date = end_date - timedelta(days=lookback_days)
    raw_end_date = end_date - timedelta(days=1)  # 昨日まで
    
    # 予約: end_date当日まで（当日予約は特徴量として使用）
    reserve_start_date = end_date - timedelta(days=lookback_days)
    reserve_end_date = end_date if include_eval_reserve else end_date - timedelta(days=1)
    
    logger.info(f"=== Data Extraction for Lookback Experiment ===")
    logger.info(f"end_date (target): {end_date}")
    logger.info(f"lookback_days: {lookback_days}")
    logger.info(f"Raw (actuals): {raw_start_date} to {raw_end_date} (end_date-1まで、リーク防止)")
    logger.info(f"Reserve: {reserve_start_date} to {reserve_end_date}")
    
    # 出力ディレクトリ作成
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    engine = sqlalchemy.create_engine(connection_string)
    
    # ========================================
    # 1. 実績データ抽出
    # ========================================
    raw_sql = text("""
        SELECT 
            slip_date AS "伝票日付",
            item_name AS "品名",
            net_weight AS "正味重量"
        FROM stg.v_active_shogun_flash_receive
        WHERE slip_date >= :start_date 
          AND slip_date <= :end_date
          AND net_weight IS NOT NULL
          AND item_name IS NOT NULL
        ORDER BY slip_date, item_name
    """)
    
    logger.info(f"[SQL] Raw query: slip_date BETWEEN {raw_start_date} AND {raw_end_date}")
    
    with engine.connect() as conn:
        raw_df = pd.read_sql(raw_sql, conn, params={
            "start_date": raw_start_date,
            "end_date": raw_end_date
        })
    
    # 日付型変換
    raw_df["伝票日付"] = pd.to_datetime(raw_df["伝票日付"]).dt.date
    
    # 重量をfloat型に変換
    raw_df["正味重量"] = pd.to_numeric(raw_df["正味重量"], errors="coerce")
    
    # 統計情報
    raw_record_count = len(raw_df)
    raw_date_min = raw_df["伝票日付"].min() if raw_record_count > 0 else None
    raw_date_max = raw_df["伝票日付"].max() if raw_record_count > 0 else None
    raw_unique_days = raw_df["伝票日付"].nunique() if raw_record_count > 0 else 0
    avg_weight_kg = raw_df["正味重量"].mean() if raw_record_count > 0 else 0.0
    
    logger.info(f"[Raw] Records: {raw_record_count}, Days: {raw_unique_days}")
    logger.info(f"[Raw] Date range: {raw_date_min} to {raw_date_max}")
    logger.info(f"[Raw] Avg weight: {avg_weight_kg:.2f} kg")
    
    # 異常検知: 平均重量が極端に大きい/小さい場合は警告
    if avg_weight_kg > 10000:
        logger.warning(f"[WARN] Avg weight {avg_weight_kg:.2f} kg is unusually high. Check for unit issues.")
    elif avg_weight_kg < 1:
        logger.warning(f"[WARN] Avg weight {avg_weight_kg:.2f} kg is unusually low. Check for unit issues.")
    
    # CSV保存
    raw_csv_path = output_dir / "raw.csv"
    raw_df.to_csv(raw_csv_path, index=False, encoding="utf-8")
    logger.info(f"[Raw] Saved to: {raw_csv_path}")
    
    # ========================================
    # 2. 予約データ抽出
    # ========================================
    reserve_sql = text("""
        SELECT 
            date AS "予約日",
            reserve_trucks AS "台数",
            fixed_customer_count AS "固定客",
            total_customer_count
        FROM mart.v_reserve_daily_features
        WHERE date >= :start_date 
          AND date <= :end_date
        ORDER BY date
    """)
    
    logger.info(f"[SQL] Reserve query: date BETWEEN {reserve_start_date} AND {reserve_end_date}")
    
    with engine.connect() as conn:
        reserve_df = pd.read_sql(reserve_sql, conn, params={
            "start_date": reserve_start_date,
            "end_date": reserve_end_date
        })
    
    # 日付型変換
    reserve_df["予約日"] = pd.to_datetime(reserve_df["予約日"]).dt.date
    
    # 数値型変換
    reserve_df["台数"] = pd.to_numeric(reserve_df["台数"], errors="coerce")
    reserve_df["固定客"] = pd.to_numeric(reserve_df["固定客"], errors="coerce")
    reserve_df["total_customer_count"] = pd.to_numeric(reserve_df["total_customer_count"], errors="coerce")
    
    # 統計情報
    reserve_record_count = len(reserve_df)
    reserve_date_min = reserve_df["予約日"].min() if reserve_record_count > 0 else None
    reserve_date_max = reserve_df["予約日"].max() if reserve_record_count > 0 else None
    
    logger.info(f"[Reserve] Records: {reserve_record_count}")
    logger.info(f"[Reserve] Date range: {reserve_date_min} to {reserve_date_max}")
    
    # CSV保存
    reserve_csv_path = output_dir / "reserve.csv"
    reserve_df.to_csv(reserve_csv_path, index=False, encoding="utf-8")
    logger.info(f"[Reserve] Saved to: {reserve_csv_path}")
    
    return ExtractionResult(
        raw_csv_path=raw_csv_path,
        reserve_csv_path=reserve_csv_path,
        raw_record_count=raw_record_count,
        raw_date_min=raw_date_min,
        raw_date_max=raw_date_max,
        raw_unique_days=raw_unique_days,
        reserve_record_count=reserve_record_count,
        reserve_date_min=reserve_date_min,
        reserve_date_max=reserve_date_max,
        avg_weight_kg=avg_weight_kg,
    )


def validate_extraction(result: ExtractionResult, expected_lookback_days: int) -> bool:
    """
    抽出結果の妥当性を検証する。
    
    Args:
        result: 抽出結果
        expected_lookback_days: 期待するlookback日数
    
    Returns:
        True if valid, False otherwise
    """
    is_valid = True
    
    # 実績日数チェック（週末・祝日で欠損があるので、期待の70%以上あればOK）
    expected_min_days = int(expected_lookback_days * 0.5)  # 営業日を考慮して50%
    if result.raw_unique_days < expected_min_days:
        logger.warning(
            f"[VALIDATION] Raw unique days ({result.raw_unique_days}) "
            f"is less than expected minimum ({expected_min_days})"
        )
        is_valid = False
    
    # 平均重量の異常検知
    if result.avg_weight_kg > 10000 or result.avg_weight_kg < 1:
        logger.warning(f"[VALIDATION] Avg weight ({result.avg_weight_kg:.2f} kg) is abnormal")
        is_valid = False
    
    # 予約データの存在確認
    if result.reserve_record_count == 0:
        logger.warning("[VALIDATION] No reserve data found")
        is_valid = False
    
    return is_valid


if __name__ == "__main__":
    # テスト実行
    import sys
    from datetime import datetime
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    
    if len(sys.argv) < 3:
        print("Usage: python db_extract.py <connection_string> <end_date> [lookback_days]")
        print("Example: python db_extract.py 'postgresql+psycopg://...' 2025-12-17 360")
        sys.exit(1)
    
    conn_str = sys.argv[1]
    end_date = datetime.strptime(sys.argv[2], "%Y-%m-%d").date()
    lookback_days = int(sys.argv[3]) if len(sys.argv) > 3 else 360
    
    output_dir = Path(f"tmp/experiments/lookback/test_LB{lookback_days}")
    
    result = extract_experiment_data(
        end_date=end_date,
        lookback_days=lookback_days,
        output_dir=output_dir,
        connection_string=conn_str,
    )
    
    print(f"\n=== Extraction Result ===")
    print(f"Raw CSV: {result.raw_csv_path}")
    print(f"Reserve CSV: {result.reserve_csv_path}")
    print(f"Raw records: {result.raw_record_count}")
    print(f"Raw days: {result.raw_unique_days}")
    print(f"Avg weight: {result.avg_weight_kg:.2f} kg")
    
    is_valid = validate_extraction(result, lookback_days)
    print(f"Validation: {'PASS' if is_valid else 'FAIL'}")
