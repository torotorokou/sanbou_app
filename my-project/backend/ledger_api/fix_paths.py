#!/usr/bin/env python3
"""
パス修正スクリプト
/backend パスを /backend に一括修正します
"""

import os
import re
from pathlib import Path


def fix_hardcoded_paths():
    """ハードコードされた /backend パスを /backend に修正"""

    # 修正対象のファイル拡張子
    extensions = [".py", ".yaml", ".yml", ".json", ".txt", ".log"]

    # 検索・置換パターン
    patterns = [
        (r"/backend", "/backend"),
        (r'"/backend', '"/backend'),
        (r"'/backend", "'/backend"),
        (r'base_dir\s*=\s*["\']?/backend["\']?', 'base_dir = "/backend"'),
        (r'BASE_DIR.*=.*["\']?/backend["\']?', 'BASE_DIR = "/backend"'),
    ]

    fixed_files = []

    print("🔍 パス修正を開始します...")

    for root, dirs, files in os.walk("/backend"):
        # __pycache__ などは除外
        if "__pycache__" in root or ".git" in root:
            continue

        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                file_path = Path(root) / file
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    original_content = content

                    # パターンを順次適用
                    for old_pattern, new_pattern in patterns:
                        content = re.sub(old_pattern, new_pattern, content)

                    # 変更があった場合のみファイルを更新
                    if content != original_content:
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(content)
                        fixed_files.append(str(file_path))
                        print(f"✅ 修正完了: {file_path}")

                except Exception as e:
                    print(f"❌ エラー {file_path}: {e}")

    return fixed_files


def check_existing_paths():
    """現在のデータファイル構造を確認"""
    print("\n📁 データファイル構造を確認中...")

    # CSVファイルを検索
    csv_files = []
    for root, dirs, files in os.walk("/backend"):
        for file in files:
            if file.endswith(".csv"):
                csv_files.append(os.path.join(root, file))

    print(f"📊 発見されたCSVファイル数: {len(csv_files)}")
    for csv_file in csv_files[:10]:  # 最初の10件を表示
        print(f"   {csv_file}")
    if len(csv_files) > 10:
        print(f"   ... and {len(csv_files) - 10} more CSV files")

    # dataディレクトリを検索
    data_dirs = []
    for root, dirs, files in os.walk("/backend"):
        if "data" in dirs:
            data_dirs.append(os.path.join(root, "data"))

    print(f"\n📂 発見されたdataディレクトリ数: {len(data_dirs)}")
    for data_dir in data_dirs:
        print(f"   {data_dir}")

    return csv_files, data_dirs


def check_work_app_references():
    """/backend への参照を検索"""
    print("\n🔍 /backend への参照を検索中...")

    references = []
    for root, dirs, files in os.walk("/backend"):
        if "__pycache__" in root:
            continue

        for file in files:
            if file.endswith((".py", ".yaml", ".yml", ".json", ".txt")):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    if "/backend" in content:
                        # 行番号も取得
                        lines = content.split("\n")
                        for i, line in enumerate(lines, 1):
                            if "/backend" in line:
                                references.append((file_path, i, line.strip()))

                except Exception as e:
                    pass

    print(f"🔍 /backend への参照数: {len(references)}")
    for ref in references[:15]:  # 最初の15件を表示
        file_path, line_num, line_content = ref
        print(f"   {file_path}:{line_num} - {line_content}")

    if len(references) > 15:
        print(f"   ... and {len(references) - 15} more references")

    return references


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 ディレクトリパス修正スクリプトを開始")
    print("=" * 60)

    # 1. 現在の状況を確認
    csv_files, data_dirs = check_existing_paths()
    references = check_work_app_references()

    # 2. パス修正を実行
    fixed_files = fix_hardcoded_paths()

    # 3. 結果をレポート
    print("\n" + "=" * 60)
    print("📊 修正完了レポート")
    print("=" * 60)
    print(f"✅ 修正されたファイル数: {len(fixed_files)}")
    print(f"📊 発見されたCSVファイル数: {len(csv_files)}")
    print(f"📂 発見されたdataディレクトリ数: {len(data_dirs)}")
    print(f"🔍 /backend参照数（修正前）: {len(references)}")

    print("\n🎉 パス修正が完了しました！")
    print("=" * 60)
