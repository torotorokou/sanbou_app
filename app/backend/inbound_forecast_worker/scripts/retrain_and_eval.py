#!/usr/bin/env python3
"""
軽量なラッパースクリプト：再学習（WFCV含む）→評価→推論 の最小ワークフローを提供します。
- 実際の学習・評価はワークスペース上の既存スクリプトを呼び出します。
- "--quick" をつけると bootstrap_iters を下げるなどして短時間でスモークを実行します。

使い方例:
  python3 scripts/retrain_and_eval.py --quick
  python3 scripts/retrain_and_eval.py --bootstrap-iters 50 --n-jobs 2

注意: 本スクリプトは上席提出用の最小ランナーです。重い本番学習を行う場合はリソースを確保してください。
"""
from __future__ import annotations
import argparse, subprocess, os, json, sys

import pandas as pd

# 提出フォルダ内での相対パス解決
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SCRIPTS_DIR = os.path.join(BASE_DIR, 'scripts')
DATA_DIR = os.path.join(BASE_DIR, 'data')
OUT_DIR = os.path.join(DATA_DIR, 'output', 'final_fast_balanced')

def prepare_dummy_daily_data(input_csv, output_csv):
    """
    日次合計データ(date, weight_t)を、train_daily_model.pyが要求する
    品目別形式(伝票日付, 品名, 正味重量)に変換する。
    品名はダミーとして 'Total' を使用する。
    """
    df = pd.read_csv(input_csv)
    # 日付列の特定
    date_col = 'date' if 'date' in df.columns else df.columns[0]
    weight_col = 'weight_t' if 'weight_t' in df.columns else df.columns[1]
    
    df_out = pd.DataFrame({
        '伝票日付': df[date_col],
        '品名': 'Total',
        '正味重量': df[weight_col]
    })
    df_out.to_csv(output_csv, index=False)
    print(f"Created dummy item-level data at {output_csv}")

def run(cmd, fout=None):
    print('\n$', ' '.join(cmd))
    if fout:
        with open(fout, 'a') as fh:
            p = subprocess.Popen(cmd, stdout=fh, stderr=subprocess.STDOUT)
            p.wait()
    else:
        p = subprocess.Popen(cmd)
        p.wait()
    
    if p.returncode != 0:
        raise SystemExit(f"Command failed: {' '.join(cmd)} (rc={p.returncode})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--quick', action='store_true', help='Run a short smoke (low bootstrap iters)')
    ap.add_argument('--bootstrap-iters', type=int, default=None)
    ap.add_argument('--n-jobs', type=int, default=1)
    ap.add_argument('--log', type=str, default=None)
    # 新規: パス制御用引数（worker実行に対応）
    ap.add_argument('--raw-csv', type=str, default=None, help='Path to raw item-level CSV (伝票日付,品名,正味重量)')
    ap.add_argument('--reserve-csv', type=str, default=None, help='Path to reserve CSV (予約日,台数,固定客)')
    ap.add_argument('--out-dir', type=str, default=None, help='Output directory for model bundle and walkforward results')
    ap.add_argument('--pred-out-csv', type=str, default=None, help='Path to save t+1 prediction CSV')
    ap.add_argument('--start-date', type=str, default=None, help='Prediction start date (YYYY-MM-DD) for t+1')
    ap.add_argument('--end-date', type=str, default=None, help='Prediction end date (YYYY-MM-DD) for t+1')
    
    # DB直接取得モード（CSV廃止）
    ap.add_argument('--use-db', action='store_true', help='DBから直接データ取得（CSVを使わない）')
    ap.add_argument('--db-connection-string', type=str, default=None, help='PostgreSQL接続文字列')
    ap.add_argument('--actuals-start-date', type=str, default=None, help='実績データ開始日（YYYY-MM-DD）')
    ap.add_argument('--actuals-end-date', type=str, default=None, help='実績データ終了日（YYYY-MM-DD）')
    ap.add_argument('--reserve-start-date', type=str, default=None, help='予約データ開始日（YYYY-MM-DD）')
    ap.add_argument('--reserve-end-date', type=str, default=None, help='予約データ終了日（YYYY-MM-DD）')
    
    args = ap.parse_args()

    # ログファイルのパス設定
    if args.log is None:
        log_path = os.path.join(BASE_DIR, 'output', 'retrain_smoke.out')
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
    else:
        log_path = args.log

    # determine training command
    train_script = os.path.join(SCRIPTS_DIR, 'train_daily_model.py')
    if not os.path.exists(train_script):
        print(f'Training script not found: {train_script}'); sys.exit(1)

    # 入力データの準備（DB直接モードではCSVを準備しない）
    # 優先: --use-db（DB直接取得モード）
    # 次点: --raw-csv引数
    # 次点: 20240501-20250422.csv (明細データ)
    # 最終: 01_daily_clean.csv (合計データ) -> ダミー変換
    
    target_csv = None
    reserve_csv = None
    
    if args.use_db:
        # DB直接取得モード: CSVファイルを準備しない
        print("Using DB direct access mode (--use-db)")
        target_csv = None  # CSVは使わない
        reserve_csv = None  # CSVは使わない
    elif args.raw_csv:
        print(f"Using raw-csv from argument: {args.raw_csv}")
        target_csv = args.raw_csv
        # reserve CSV（引数優先、未指定時はデフォルト）
        if args.reserve_csv:
            reserve_csv = args.reserve_csv
        else:
            reserve_csv = os.path.join(DATA_DIR, 'input', 'yoyaku_data.csv')
    else:
        # CSV従来モード（デフォルト）
        detail_csv_path = os.path.join(DATA_DIR, 'input', '20240501-20250422.csv')
        raw_csv_path = os.path.join(DATA_DIR, 'input', '01_daily_clean.csv')
        dummy_csv_path = os.path.join(DATA_DIR, 'input', '01_daily_clean_dummy_item.csv')
        
        if os.path.exists(detail_csv_path):
            print(f"Using detail data: {detail_csv_path}")
            target_csv = detail_csv_path
        else:
            print(f"Using aggregate data (converting to dummy): {raw_csv_path}")
            prepare_dummy_daily_data(raw_csv_path, dummy_csv_path)
            target_csv = dummy_csv_path
        
        # reserve CSV（引数優先、未指定時はデフォルト）
        if args.reserve_csv:
            reserve_csv = args.reserve_csv
        else:
            reserve_csv = os.path.join(DATA_DIR, 'input', 'yoyaku_data.csv')
    
    # 出力ディレクトリ（引数優先、未指定時はデフォルト）
    if args.out_dir:
        out_dir = args.out_dir
        os.makedirs(out_dir, exist_ok=True)
    else:
        out_dir = OUT_DIR
    
    # build command
    # READMEの推奨コマンドをベースに構築
    cmd_train = [
        sys.executable, train_script,
        '--out-dir', out_dir,
        '--save-bundle', os.path.join(out_dir, 'model_bundle.joblib'),
        '--n-jobs', str(args.n_jobs),
        '--no-plots'
    ]
    
    # DB直接取得モードまたはCSVモード
    if args.use_db:
        cmd_train.extend(['--use-db'])
        if args.db_connection_string:
            cmd_train.extend(['--db-connection-string', args.db_connection_string])
        if args.actuals_start_date:
            cmd_train.extend(['--actuals-start-date', args.actuals_start_date])
        if args.actuals_end_date:
            cmd_train.extend(['--actuals-end-date', args.actuals_end_date])
        if args.reserve_start_date:
            cmd_train.extend(['--reserve-start-date', args.reserve_start_date])
        if args.reserve_end_date:
            cmd_train.extend(['--reserve-end-date', args.reserve_end_date])
    else:
        # CSV従来モード
        cmd_train.extend([
            '--raw-csv', target_csv,
            '--reserve-csv', reserve_csv,
        ])
    
    # 列名指定（共通）
    cmd_train.extend([
        '--raw-date-col', '伝票日付', '--raw-item-col', '品名', '--raw-weight-col', '正味重量',
        '--reserve-date-col', '予約日', '--reserve-count-col', '台数', '--reserve-fixed-col', '固定客',
    ])

    if args.quick:
        # クイックモード: 分割数を減らし、木の本数を減らす
        cmd_train.extend(['--n-splits', '2'])
        cmd_train.extend(['--rf-n-estimators', '10'])
        cmd_train.extend(['--gbr-n-estimators', '10'])

    print(f"Starting training... (log: {log_path})")
    try:
        run(cmd_train, fout=log_path)
    except SystemExit as e:
        print('Training failed; see log:', log_path); raise

    print("Training completed.")

    # 推論 (t+1)
    predict_script = os.path.join(SCRIPTS_DIR, 'daily_tplus1_predict.py')
    if os.path.exists(predict_script):
        # 予測出力先（引数優先、未指定時はデフォルト）
        if args.pred_out_csv:
            pred_out_csv = args.pred_out_csv
        else:
            pred_out_csv = os.path.join(DATA_DIR, 'output', 'tplus1_pred.csv')
        
        os.makedirs(os.path.dirname(pred_out_csv), exist_ok=True)
        
        cmd_pred = [
            sys.executable, predict_script,
            '--bundle', os.path.join(out_dir, 'model_bundle.joblib'),
            '--res-walk-csv', os.path.join(out_dir, 'res_walkforward.csv'),
            '--out-csv', pred_out_csv
        ]
        
        # DB直接取得モードまたはCSVモード
        if args.use_db:
            cmd_pred.extend(['--use-db'])
            if args.db_connection_string:
                cmd_pred.extend(['--db-connection-string', args.db_connection_string])
            if args.reserve_start_date:
                cmd_pred.extend(['--reserve-start-date', args.reserve_start_date])
            if args.reserve_end_date:
                cmd_pred.extend(['--reserve-end-date', args.reserve_end_date])
        else:
            # CSV従来モード
            cmd_pred.extend(['--reserve-csv', reserve_csv])
        
        # --start-date / --end-date が指定されていれば追加
        if args.start_date:
            cmd_pred.extend(['--start-date', args.start_date])
        if args.end_date:
            cmd_pred.extend(['--end-date', args.end_date])
        
        print("Starting prediction...")
        run(cmd_pred, fout=log_path)
        print("Prediction completed.")

if __name__ == '__main__':
    main()
