#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_lookback_sweep.py - 学習期間（lookback）別精度比較実験ランナー

目的:
- 学習に使う過去日数（lookback window）を変えて精度を比較
- 最適な学習期間を特定するための実験

使用方法:
    python3 run_lookback_sweep.py \\
        --end-date 2025-12-17 \\
        --lookbacks 60,90,120,180,270,360 \\
        --eval-days 90 \\
        --quick

出力:
    tmp/experiments/lookback/
    ├── LB060/
    │   ├── raw.csv
    │   ├── reserve.csv
    │   ├── model_bundle.joblib
    │   ├── scores_walkforward.json
    │   └── run.log
    ├── LB090/
    │   └── ...
    ├── results.csv
    └── report.md
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict

# 親ディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from exp_utils.db_extract import extract_experiment_data, validate_extraction, ExtractionResult

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class ExperimentResult:
    """1回の実験結果"""
    lookback_days: int
    eval_days: int
    status: str  # "success", "failed", "skipped"
    r2_total: Optional[float] = None
    r2_sum_only: Optional[float] = None
    mae_kg: Optional[float] = None
    mae_sum_only_kg: Optional[float] = None
    train_seconds: Optional[float] = None
    raw_records: Optional[int] = None
    raw_days: Optional[int] = None
    reserve_records: Optional[int] = None
    error: Optional[str] = None
    notes: Optional[str] = None


def parse_scores_json(scores_path: Path) -> Dict[str, Any]:
    """scores_walkforward.jsonをパースして指標を取得"""
    if not scores_path.exists():
        return {}
    
    with open(scores_path, "r") as f:
        return json.load(f)


def run_single_experiment(
    lookback_days: int,
    end_date: date,
    eval_days: int,
    output_base_dir: Path,
    connection_string: str,
    train_script_path: Path,
    quick: bool = False,
    n_jobs: int = 1,
) -> ExperimentResult:
    """
    1つのlookback設定で実験を実行
    
    Args:
        lookback_days: 学習に使う過去日数
        end_date: 評価基準日
        eval_days: 評価期間（日数）
        output_base_dir: 出力ベースディレクトリ
        connection_string: DB接続文字列
        train_script_path: train_daily_model.pyのパス
        quick: 軽量モードかどうか
        n_jobs: 並列数
    
    Returns:
        ExperimentResult: 実験結果
    """
    # 作業ディレクトリ
    work_dir = output_base_dir / f"LB{lookback_days:03d}"
    work_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"=" * 60)
    logger.info(f"Running experiment: lookback={lookback_days} days")
    logger.info(f"Output: {work_dir}")
    logger.info(f"=" * 60)
    
    start_time = time.time()
    
    try:
        # 1. データ抽出
        logger.info(f"[Step 1/3] Extracting data from DB...")
        extraction_result = extract_experiment_data(
            end_date=end_date,
            lookback_days=lookback_days,
            output_dir=work_dir,
            connection_string=connection_string,
            include_eval_reserve=True,
        )
        
        # 検証
        if not validate_extraction(extraction_result, lookback_days):
            logger.warning(f"Data validation failed for lookback={lookback_days}")
        
        # 2. 学習実行
        logger.info(f"[Step 2/3] Running training...")
        
        # 学習期間: 実績の開始日から終了日まで
        # eval_daysは使わない（walk-forwardで内部評価）
        actuals_start = extraction_result.raw_date_min
        actuals_end = extraction_result.raw_date_max
        reserve_start = extraction_result.reserve_date_min
        reserve_end = extraction_result.reserve_date_max
        
        cmd = [
            sys.executable,
            str(train_script_path),
            "--out-dir", str(work_dir),
            "--save-bundle", str(work_dir / "model_bundle.joblib"),
            "--use-db",
            "--db-connection-string", connection_string,
            "--actuals-start-date", str(actuals_start),
            "--actuals-end-date", str(actuals_end),
            "--reserve-start-date", str(reserve_start),
            "--reserve-end-date", str(reserve_end),
            "--raw-date-col", "伝票日付",
            "--raw-item-col", "品名",
            "--raw-weight-col", "正味重量",
            "--reserve-date-col", "予約日",
            "--reserve-count-col", "台数",
            "--reserve-fixed-col", "固定客",
            "--n-jobs", str(n_jobs),
            "--no-plots",
        ]
        
        if quick:
            cmd.extend([
                "--n-splits", "2",
                "--rf-n-estimators", "10",
                "--gbr-n-estimators", "10",
            ])
        
        # ログファイル
        log_path = work_dir / "train.log"
        logger.info(f"Command: {' '.join(cmd[:10])}...")
        
        with open(log_path, "w") as log_file:
            process = subprocess.run(
                cmd,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                timeout=3600,  # 1時間タイムアウト
            )
        
        if process.returncode != 0:
            raise RuntimeError(f"Training failed with return code {process.returncode}")
        
        # 3. 結果取得
        logger.info(f"[Step 3/3] Collecting results...")
        
        scores_path = work_dir / "scores_walkforward.json"
        scores = parse_scores_json(scores_path)
        
        elapsed = time.time() - start_time
        
        result = ExperimentResult(
            lookback_days=lookback_days,
            eval_days=eval_days,
            status="success",
            r2_total=scores.get("R2_total"),
            r2_sum_only=scores.get("R2_sum_only"),
            mae_kg=scores.get("MAE_total"),
            mae_sum_only_kg=scores.get("MAE_sum_only"),
            train_seconds=elapsed,
            raw_records=extraction_result.raw_record_count,
            raw_days=extraction_result.raw_unique_days,
            reserve_records=extraction_result.reserve_record_count,
            notes=f"quick={quick}",
        )
        
        logger.info(f"✅ Completed: R2={result.r2_total:.4f}, MAE={result.mae_kg:.0f}kg in {elapsed:.1f}s")
        return result
        
    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = str(e)[:500]
        logger.error(f"❌ Failed: {error_msg}")
        
        return ExperimentResult(
            lookback_days=lookback_days,
            eval_days=eval_days,
            status="failed",
            train_seconds=elapsed,
            error=error_msg,
        )


def generate_report(
    results: List[ExperimentResult],
    output_dir: Path,
    end_date: date,
    eval_days: int,
    quick: bool,
) -> Path:
    """
    実験結果のMarkdownレポートを生成
    
    Args:
        results: 実験結果リスト
        output_dir: 出力ディレクトリ
        end_date: 評価基準日
        eval_days: 評価期間
        quick: 軽量モードかどうか
    
    Returns:
        レポートファイルのパス
    """
    report_path = output_dir / "report.md"
    
    # 成功した結果のみ抽出
    successful = [r for r in results if r.status == "success" and r.r2_total is not None]
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Lookback期間別精度比較レポート\n\n")
        f.write(f"**生成日時**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## 1. 実験設定\n\n")
        f.write(f"| 項目 | 値 |\n")
        f.write(f"|------|-----|\n")
        f.write(f"| 評価基準日 (end_date) | {end_date} |\n")
        f.write(f"| 評価期間 (eval_days) | {eval_days}日 |\n")
        f.write(f"| Lookback候補 | {', '.join(str(r.lookback_days) for r in results)}日 |\n")
        f.write(f"| 軽量モード (quick) | {'Yes' if quick else 'No'} |\n")
        f.write(f"| 実行件数 | {len(results)}件 |\n")
        f.write(f"| 成功件数 | {len(successful)}件 |\n\n")
        
        f.write("## 2. 結果一覧\n\n")
        f.write("| Lookback | R2_total | R2_sum_only | MAE (kg) | MAE_sum (kg) | 実績日数 | 時間(s) | Status |\n")
        f.write("|----------|----------|-------------|----------|--------------|----------|---------|--------|\n")
        
        for r in results:
            r2_total = f"{r.r2_total:.4f}" if r.r2_total is not None else "-"
            r2_sum = f"{r.r2_sum_only:.4f}" if r.r2_sum_only is not None else "-"
            mae = f"{r.mae_kg:,.0f}" if r.mae_kg is not None else "-"
            mae_sum = f"{r.mae_sum_only_kg:,.0f}" if r.mae_sum_only_kg is not None else "-"
            raw_days = str(r.raw_days) if r.raw_days is not None else "-"
            train_time = f"{r.train_seconds:.1f}" if r.train_seconds is not None else "-"
            status_icon = "✅" if r.status == "success" else "❌"
            
            f.write(f"| {r.lookback_days}日 | {r2_total} | {r2_sum} | {mae} | {mae_sum} | {raw_days} | {train_time} | {status_icon} |\n")
        
        f.write("\n")
        
        if successful:
            f.write("## 3. ベスト結果\n\n")
            
            # R2最大
            best_r2 = max(successful, key=lambda x: x.r2_total or -999)
            f.write(f"### R2最大: lookback={best_r2.lookback_days}日\n")
            f.write(f"- R2_total: **{best_r2.r2_total:.4f}**\n")
            f.write(f"- MAE: {best_r2.mae_kg:,.0f} kg\n\n")
            
            # MAE最小
            best_mae = min(successful, key=lambda x: x.mae_kg or 999999)
            f.write(f"### MAE最小: lookback={best_mae.lookback_days}日\n")
            f.write(f"- MAE: **{best_mae.mae_kg:,.0f} kg**\n")
            f.write(f"- R2_total: {best_mae.r2_total:.4f}\n\n")
            
            # Top 3 by R2
            f.write("### Top 3 (R2順)\n\n")
            top3 = sorted(successful, key=lambda x: x.r2_total or -999, reverse=True)[:3]
            for i, r in enumerate(top3, 1):
                f.write(f"{i}. lookback={r.lookback_days}日: R2={r.r2_total:.4f}, MAE={r.mae_kg:,.0f}kg\n")
            
            f.write("\n## 4. 推奨設定\n\n")
            
            # 推奨ロジック: R2が最大でMAEも妥当な範囲
            recommended = best_r2
            f.write(f"**推奨lookback: {recommended.lookback_days}日**\n\n")
            f.write("理由:\n")
            f.write(f"- R2_total = {recommended.r2_total:.4f} で最も高い説明力\n")
            f.write(f"- MAE = {recommended.mae_kg:,.0f} kg で実用的な誤差範囲\n\n")
            
            f.write("## 5. 注意事項\n\n")
            f.write("- lookbackが短すぎる（<90日）: 学習データ不足で過学習リスク\n")
            f.write("- lookbackが長すぎる（>540日）: 古いデータの分布変化に追従できない可能性\n")
            f.write("- 最終決定は実運用の安定性も考慮してください\n")
        else:
            f.write("## 3. 結果なし\n\n")
            f.write("成功した実験がありませんでした。エラーログを確認してください。\n")
        
        # エラー一覧
        failed = [r for r in results if r.status == "failed"]
        if failed:
            f.write("\n## 6. エラー一覧\n\n")
            for r in failed:
                f.write(f"### lookback={r.lookback_days}日\n")
                f.write(f"```\n{r.error}\n```\n\n")
    
    logger.info(f"Report saved to: {report_path}")
    return report_path


def save_results_csv(results: List[ExperimentResult], output_path: Path):
    """結果をCSVに保存"""
    import csv
    
    fieldnames = [
        "lookback_days", "eval_days", "status",
        "r2_total", "r2_sum_only", "mae_kg", "mae_sum_only_kg",
        "train_seconds", "raw_records", "raw_days", "reserve_records",
        "error", "notes"
    ]
    
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow(asdict(r))
    
    logger.info(f"Results CSV saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="学習期間（lookback）別精度比較実験ランナー"
    )
    parser.add_argument(
        "--end-date", type=str, required=True,
        help="評価基準日（YYYY-MM-DD）"
    )
    parser.add_argument(
        "--lookbacks", type=str, default="60,90,120,180,270,360,540",
        help="カンマ区切りのlookback日数リスト（デフォルト: 60,90,120,180,270,360,540）"
    )
    parser.add_argument(
        "--eval-days", type=int, default=90,
        help="評価期間の日数（デフォルト: 90）"
    )
    parser.add_argument(
        "--n-jobs", type=int, default=1,
        help="並列数（デフォルト: 1）"
    )
    parser.add_argument(
        "--quick", action="store_true",
        help="軽量モード（木の本数、split数を下げる）"
    )
    parser.add_argument(
        "--db-connection-string", type=str, default=None,
        help="DB接続文字列（未指定時は環境変数DATABASE_URLを使用）"
    )
    parser.add_argument(
        "--output-dir", type=str, default=None,
        help="出力ディレクトリ（デフォルト: tmp/experiments/lookback）"
    )
    
    args = parser.parse_args()
    
    # パース
    end_date = datetime.strptime(args.end_date, "%Y-%m-%d").date()
    lookbacks = [int(x.strip()) for x in args.lookbacks.split(",")]
    
    # 接続文字列
    connection_string = args.db_connection_string or os.getenv("DATABASE_URL")
    if not connection_string:
        logger.error("DB connection string not provided. Use --db-connection-string or set DATABASE_URL")
        sys.exit(1)
    
    # 出力ディレクトリ
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        # デフォルト: プロジェクトルートの tmp/experiments/lookback
        script_dir = Path(__file__).parent
        project_root = script_dir.parent.parent.parent.parent.parent  # sanbou_app
        output_dir = project_root / "tmp" / "experiments" / "lookback"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # train_daily_model.pyのパス
    train_script = Path(__file__).parent.parent / "train_daily_model.py"
    if not train_script.exists():
        logger.error(f"Train script not found: {train_script}")
        sys.exit(1)
    
    logger.info("=" * 70)
    logger.info("Lookback Sweep Experiment")
    logger.info("=" * 70)
    logger.info(f"End date: {end_date}")
    logger.info(f"Lookbacks: {lookbacks}")
    logger.info(f"Eval days: {args.eval_days}")
    logger.info(f"Quick mode: {args.quick}")
    logger.info(f"Output: {output_dir}")
    logger.info("=" * 70)
    
    results: List[ExperimentResult] = []
    
    for i, lookback in enumerate(lookbacks, 1):
        logger.info(f"\n[{i}/{len(lookbacks)}] Starting lookback={lookback} days...")
        
        result = run_single_experiment(
            lookback_days=lookback,
            end_date=end_date,
            eval_days=args.eval_days,
            output_base_dir=output_dir,
            connection_string=connection_string,
            train_script_path=train_script,
            quick=args.quick,
            n_jobs=args.n_jobs,
        )
        results.append(result)
        
        # 中間結果を保存（途中で中断しても結果が残る）
        save_results_csv(results, output_dir / "results.csv")
    
    # 最終レポート生成
    generate_report(
        results=results,
        output_dir=output_dir,
        end_date=end_date,
        eval_days=args.eval_days,
        quick=args.quick,
    )
    
    # サマリ出力
    successful = [r for r in results if r.status == "success"]
    logger.info("\n" + "=" * 70)
    logger.info("EXPERIMENT COMPLETED")
    logger.info("=" * 70)
    logger.info(f"Total: {len(results)}, Success: {len(successful)}, Failed: {len(results) - len(successful)}")
    
    if successful:
        best = max(successful, key=lambda x: x.r2_total or -999)
        logger.info(f"Best R2: lookback={best.lookback_days}d, R2={best.r2_total:.4f}, MAE={best.mae_kg:,.0f}kg")
    
    logger.info(f"Results: {output_dir / 'results.csv'}")
    logger.info(f"Report: {output_dir / 'report.md'}")


if __name__ == "__main__":
    main()
