#!/usr/bin/env python3
"""
売上収支表の有価物計算検証スクリプト

修正前後で有価物の値が正しく計算されることを確認します。

使用方法:
  docker compose -f docker/docker-compose.dev.yml -p local_dev exec core_api \
    python /test/verify_balance_sheet_fix.py
"""
import os
import sys

import pandas as pd

# Dockerコンテナ内で実行されることを想定
try:
    from app.infra.report_utils import get_unit_price_table_csv
    from app.infra.report_utils.formatters import multiply_columns, summary_apply
    from app.infra.report_utils.template_config import get_template_config
    from app.infra.report_utils.template_loader import load_master_and_template
except ImportError:
    print("❌ このスクリプトはDockerコンテナ内で実行する必要があります")
    print("実行方法:")
    print("  docker compose -f docker/docker-compose.dev.yml -p local_dev exec ledger_api \\")
    print("    python /test/verify_balance_sheet_fix.py")
    sys.exit(1)


def load_test_data():
    """テストデータを読み込む"""
    # Dockerコンテナ内のパス
    base_path = "/test"

    # ヤード一覧を読み込み
    yard_path = os.path.join(base_path, "ヤード一覧_20251202_093735.csv")
    df_yard = pd.read_csv(yard_path, encoding="utf-8-sig")

    # 出荷一覧を読み込み
    shipment_path = os.path.join(base_path, "出荷一覧_20251202_093724.csv")
    df_shipment = pd.read_csv(shipment_path, encoding="utf-8-sig")

    print("✅ テストデータ読み込み完了")
    print(f"   - ヤード: {len(df_yard)}行")
    print(f"   - 出荷: {len(df_shipment)}行")
    print()

    return df_yard, df_shipment


def verify_yard_valuable_material(df_yard):
    """ヤード有価物の計算を検証"""
    print("=" * 70)
    print("🔍 ヤード有価物の計算検証")
    print("=" * 70)

    config = get_template_config()["balance_sheet"]
    master_path = config["master_csv_path"]["yuka_yard"]
    master_df = load_master_and_template(master_path)

    print("\n【ステップ1】品名マスタ")
    print(master_df)
    print()

    # 有価物のみフィルタ
    df_yard_valuable = df_yard[df_yard["種類名"] == "有価物"].copy()
    print(f"【ステップ2】ヤードデータから有価物をフィルタ: {len(df_yard_valuable)}行")
    print(df_yard_valuable[["品名", "数量"]].head(10))
    print()

    # ① 品名別に数量を集計
    yard_summary = df_yard_valuable.groupby("品名", as_index=False)["数量"].sum()
    print("【ステップ3】品名別数量集計")
    print(yard_summary)
    print()

    # ② 単価テーブルから単価を取得
    unit_price_df = get_unit_price_table_csv()
    unit_price_valuable = unit_price_df[unit_price_df["必要項目"] == "有価物"].copy()
    print("【ステップ4】単価テーブル（有価物のみ）")
    print(unit_price_valuable[["品名", "設定単価"]])
    print()

    # ③ 単価をマージ
    yard_with_price = pd.merge(
        yard_summary, unit_price_valuable[["品名", "設定単価"]], on="品名", how="left"
    )
    print("【ステップ5】数量+単価マージ")
    print(yard_with_price)
    print()

    # ④ 数量 × 単価 = 金額
    yard_with_price["金額"] = yard_with_price["数量"] * yard_with_price["設定単価"]
    print("【ステップ6】金額計算（数量 × 単価）")
    print(yard_with_price)
    print()

    yard_total = int(yard_with_price["金額"].sum())
    print(f"✅ ヤード有価物合計: {yard_total:,}円")
    print()

    return yard_total


def verify_shipment_valuable_material(df_shipment):
    """出荷有価物の計算を検証"""
    print("=" * 70)
    print("🔍 出荷有価物の計算検証")
    print("=" * 70)

    config = get_template_config()["balance_sheet"]
    master_path = config["master_csv_path"]["yuka_shipment"]
    master_df = load_master_and_template(master_path)

    print("\n【ステップ1】業者マスタ")
    print(master_df)
    print()

    # 有価物のみフィルタ
    df_shipment_valuable = df_shipment[df_shipment["種類名"] == "有価物"].copy()
    print(f"【ステップ2】出荷データから有価物をフィルタ: {len(df_shipment_valuable)}行")
    print(df_shipment_valuable[["業者名", "金額"]].head(10))
    print()

    # 金額文字列をクリーニング
    df_shipment_valuable["金額"] = (
        df_shipment_valuable["金額"].astype(str).str.replace(",", "").astype(float)
    )

    # 業者別に金額を集計
    shipment_summary = df_shipment_valuable.groupby("業者名", as_index=False)["金額"].sum()
    print("【ステップ3】業者別金額集計")
    print(shipment_summary)
    print()

    shipment_total = int(shipment_summary["金額"].sum())
    print(f"✅ 出荷有価物合計: {shipment_total:,}円")
    print()

    return shipment_total


def main():
    """メイン処理"""
    print("\n" + "=" * 70)
    print("🧪 売上収支表 有価物計算 検証スクリプト")
    print("=" * 70)
    print()

    try:
        # テストデータ読み込み
        df_yard, df_shipment = load_test_data()

        # ヤード有価物を検証
        yard_total = verify_yard_valuable_material(df_yard)

        # 出荷有価物を検証
        shipment_total = verify_shipment_valuable_material(df_shipment)

        # 合計
        total_valuable = yard_total + shipment_total

        print("=" * 70)
        print("📊 最終結果")
        print("=" * 70)
        print(f"ヤード有価物:   {yard_total:>10,}円")
        print(f"出荷有価物:     {shipment_total:>10,}円")
        print("-" * 70)
        print(f"有価物合計:     {total_valuable:>10,}円")
        print("=" * 70)
        print()

        print("✅ 検証完了！")
        print()
        print("💡 この値が旧Streamlitアプリと一致することを確認してください。")

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
