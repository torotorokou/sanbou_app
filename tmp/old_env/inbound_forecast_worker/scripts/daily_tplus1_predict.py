#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
t+1 日次予測の簡易ランチャー。

- 内部で scripts/serve_predict_model_v4_2_4.py の run_inference を呼び出します
- 予約データが無い場合は、--manual-reserve で手動指定、または --prompt-reserve で対話入力が可能

例1: 予約なし（ゼロ扱い）で t+1 を予測
  python3 scripts/daily_tplus1_predict.py \
    --bundle /works/data/output/final_fast_balanced/model_bundle.joblib \
    --res-walk-csv /works/data/output/final_fast_balanced/res_walkforward.csv \
    --out-csv /works/data/output/tplus1_pred.csv

例2: 手動で予約を指定（count,sum,fixed）
  python3 scripts/daily_tplus1_predict.py \
    --bundle /works/data/output/final_fast_balanced/model_bundle.joblib \
    --res-walk-csv /works/data/output/final_fast_balanced/res_walkforward.csv \
    --manual-reserve 2025-10-01=5,15000,0.2 \
    --out-csv /works/data/output/tplus1_pred.csv
"""

import argparse
import os
import sys
import subprocess


def main():
    ap = argparse.ArgumentParser(description='t+1 日次予測（予約の手動/対話入力に対応）')
    ap.add_argument('--bundle', required=True, help='*.joblib （final_fast_balanced の model_bundle.joblib など）')
    ap.add_argument('--out-csv', required=True, help='出力CSVパス')
    ap.add_argument('--res-walk-csv', default=None, help='バンドルに history_tail が無い場合に使う履歴CSV（res_walkforward.csv）')
    ap.add_argument('--reserve-csv', default=None, help='予約CSV（無ければ未指定でOK）')
    ap.add_argument('--reserve-date-col', default='予約日')
    ap.add_argument('--reserve-count-col', default='台数')
    ap.add_argument('--reserve-fixed-col', default='固定客')
    ap.add_argument('--manual-reserve', default=None, help="'YYYY-MM-DD=count,sum[,fixed];YYYY-MM-DD=count,sum' 形式")
    ap.add_argument('--prompt-reserve', action='store_true')
    ap.add_argument('--reserve-default-count', type=float, default=0.0)
    ap.add_argument('--reserve-default-sum', type=float, default=0.0)
    ap.add_argument('--reserve-default-fixed', type=float, default=0.0)
    ap.add_argument('--start-date', default=None, help='予測開始日（省略時は履歴の翌日をt+1として使用）')
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.out_csv) or '.', exist_ok=True)

    # サービススクリプトをサブプロセスで実行して堅牢に動かす（関数インポート依存を避ける）
    serve_path = os.path.join(os.path.dirname(__file__), 'serve_predict_model_v4_2_4.py')
    cmd = [sys.executable, serve_path,
           '--bundle', args.bundle,
           '--out-csv', args.out_csv,
           '--future-days', '1']
    if args.res_walk_csv:
        cmd += ['--res-walk-csv', args.res_walk_csv]
    if args.reserve_csv:
        cmd += ['--reserve-csv', args.reserve_csv,
                '--reserve-date-col', args.reserve_date_col,
                '--reserve-count-col', args.reserve_count_col,
                '--reserve-fixed-col', args.reserve_fixed_col]
    if args.manual_reserve:
        cmd += ['--manual-reserve', args.manual_reserve]
    if args.prompt_reserve:
        cmd += ['--prompt-reserve']
    if args.reserve_default_count is not None:
        cmd += ['--reserve-default-count', str(args.reserve_default_count)]
    if args.reserve_default_sum is not None:
        cmd += ['--reserve-default-sum', str(args.reserve_default_sum)]
    if args.reserve_default_fixed is not None:
        cmd += ['--reserve-default-fixed', str(args.reserve_default_fixed)]
    if args.start_date:
        cmd += ['--start-date', args.start_date]

    print('[INFO] launching serve script:', ' '.join(cmd))
    proc = subprocess.run(cmd, capture_output=True, text=True)
    # パイプ出力をそのまま中継
    if proc.stdout:
        print(proc.stdout, end='')
    if proc.stderr:
        print(proc.stderr, file=sys.stderr, end='')
    if proc.returncode != 0:
        print(f'[ERROR] serve script exited with code {proc.returncode}', file=sys.stderr)
        sys.exit(proc.returncode)
    # 出力が本当に生成されたか最終チェック
    if not os.path.exists(args.out_csv) or os.path.getsize(args.out_csv) == 0:
        print('[ERROR] サービススクリプトは正常終了しましたが、出力CSVが見つかりません: ', args.out_csv, file=sys.stderr)
        print('        入力バンドルに history_tail が無い場合は --res-walk-csv を指定してください。', file=sys.stderr)
        sys.exit(2)
    print('[DONE] t+1 prediction written to', args.out_csv)


if __name__ == '__main__':
    main()
