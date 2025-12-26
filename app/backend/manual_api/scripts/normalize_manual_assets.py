#!/usr/bin/env python3
"""
マニュアルアセット正規化スクリプト

目的：
- 拡張子の大文字（.PNG/.JPG/.JPEG/.WEBP）を小文字にリネーム
- index.json 内の参照パスも同時更新
- Linux/Docker環境での404エラーを防止

使い方：
  # Dry run（変更予定を表示）
  python -m manual_api.scripts.normalize_manual_assets --dry-run

  # Apply（実際に変更）
  python -m manual_api.scripts.normalize_manual_assets --apply

  # 特定ディレクトリのみ
  python -m manual_api.scripts.normalize_manual_assets --apply --target thumbs
"""

import argparse
import json
import re
import sys
from pathlib import Path


# 対象拡張子（大文字）
UPPERCASE_EXTENSIONS = [".PNG", ".JPG", ".JPEG", ".WEBP", ".GIF", ".SVG"]

# 正規化対象ディレクトリ
DEFAULT_TARGETS = ["thumbs", "videos", "flowcharts", "contents"]


class AssetNormalizer:
    """アセット正規化クラス"""

    def __init__(self, base_dir: Path, dry_run: bool = True):
        self.base_dir = base_dir
        self.dry_run = dry_run
        self.renamed_files: list[tuple[Path, Path]] = []
        self.updated_refs: dict[str, list[str]] = {}

    def normalize_directory(self, target_dir: str) -> int:
        """指定ディレクトリ内のファイル拡張子を正規化"""
        dir_path = self.base_dir / target_dir
        if not dir_path.exists():
            print(f"⚠️  ディレクトリが存在しません: {dir_path}")
            return 0

        count = 0
        for file_path in dir_path.rglob("*"):
            if not file_path.is_file():
                continue

            # 大文字拡張子を検出
            if file_path.suffix in UPPERCASE_EXTENSIONS:
                new_name = file_path.stem + file_path.suffix.lower()
                new_path = file_path.parent / new_name

                if new_path.exists() and new_path != file_path:
                    print(f"⚠️  衝突スキップ: {file_path.name} (既に小文字版が存在)")
                    continue

                self.renamed_files.append((file_path, new_path))
                count += 1

                if self.dry_run:
                    print(f"  📝 {file_path.relative_to(self.base_dir)} → {new_path.name}")
                else:
                    # Gitが大小文字変更を検知するため、一度別名にしてから戻す
                    temp_path = file_path.parent / f"_temp_{new_name}"
                    file_path.rename(temp_path)
                    temp_path.rename(new_path)
                    print(f"  ✅ {file_path.relative_to(self.base_dir)} → {new_path.name}")

        return count

    def update_index_json(self) -> int:
        """index.json 内の拡張子参照を更新"""
        index_path = self.base_dir / "index.json"
        if not index_path.exists():
            print(f"⚠️  index.json が見つかりません: {index_path}")
            return 0

        with open(index_path, encoding="utf-8") as f:
            data = json.load(f)

        original_json = json.dumps(data, ensure_ascii=False, indent=2)
        updated_json = original_json
        count = 0

        # 大文字拡張子のパスを小文字に置換
        for ext in UPPERCASE_EXTENSIONS:
            pattern = re.escape(ext)
            replacement = ext.lower()
            matches = re.findall(f"[\"']([^\"']+{pattern})[\"']", updated_json)
            if matches:
                self.updated_refs[ext] = matches
                count += len(matches)
                updated_json = re.sub(pattern, replacement, updated_json)

        if original_json != updated_json:
            if self.dry_run:
                print("\n📝 index.json の更新予定:")
                for ext, paths in self.updated_refs.items():
                    print(f"  {ext} → {ext.lower()} ({len(paths)}件)")
            else:
                data_updated = json.loads(updated_json)
                with open(index_path, "w", encoding="utf-8") as f:
                    json.dump(data_updated, f, ensure_ascii=False, indent=2)
                print(f"\n✅ index.json を更新しました ({count}件)")

        return count

    def report_summary(self) -> None:
        """実行結果サマリを出力"""
        print("\n" + "=" * 60)
        if self.dry_run:
            print("🔍 Dry Run 結果")
        else:
            print("✅ Apply 結果")
        print("=" * 60)
        print(f"リネーム対象ファイル: {len(self.renamed_files)}件")
        print(f"index.json 更新箇所: {sum(len(v) for v in self.updated_refs.values())}件")

        if self.renamed_files:
            print("\n📋 リネーム一覧:")
            for old_path, new_path in self.renamed_files[:10]:  # 最初の10件のみ
                print(f"  {old_path.name} → {new_path.name}")
            if len(self.renamed_files) > 10:
                print(f"  ... 他 {len(self.renamed_files) - 10}件")

        if not self.dry_run:
            print("\n✅ 正規化が完了しました")
            print("📌 次の手順:")
            print("  1. git status で変更を確認")
            print("  2. git add . で変更をステージング")
            print("  3. git commit -m 'normalize: 拡張子を小文字に統一'")
        else:
            print("\n💡 実際に変更するには --apply オプションを使用してください")


def main():
    parser = argparse.ArgumentParser(
        description="マニュアルアセットの拡張子を正規化（大文字→小文字）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # Dry run
  python -m manual_api.scripts.normalize_manual_assets --dry-run

  # 実際に変更
  python -m manual_api.scripts.normalize_manual_assets --apply

  # thumbs のみ変更
  python -m manual_api.scripts.normalize_manual_assets --apply --target thumbs
        """,
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="変更内容を表示するのみ（実際には変更しない）"
    )
    parser.add_argument("--apply", action="store_true", help="実際に変更を適用する")
    parser.add_argument(
        "--target",
        choices=DEFAULT_TARGETS,
        nargs="+",
        default=DEFAULT_TARGETS,
        help="対象ディレクトリを指定（デフォルト: 全て）",
    )
    parser.add_argument(
        "--base-dir", type=Path, help="manuals ディレクトリのパス（デフォルト: 自動検出）"
    )

    args = parser.parse_args()

    # dry-run も apply も指定されていない場合はエラー
    if not args.dry_run and not args.apply:
        parser.error("--dry-run または --apply のいずれかを指定してください")

    # ベースディレクトリの自動検出
    if args.base_dir:
        base_dir = args.base_dir
    else:
        # スクリプトの位置から推定
        script_dir = Path(__file__).parent
        base_dir = script_dir.parent / "local_data" / "manuals"

    if not base_dir.exists():
        print(f"❌ エラー: manuals ディレクトリが見つかりません: {base_dir}")
        print("   --base-dir オプションでパスを指定してください")
        sys.exit(1)

    print(f"📁 対象ディレクトリ: {base_dir}")
    print(f"🎯 モード: {'Dry Run（変更なし）' if args.dry_run else 'Apply（変更実行）'}")
    print(f"📂 対象: {', '.join(args.target)}")
    print()

    # 正規化実行
    normalizer = AssetNormalizer(base_dir, dry_run=args.dry_run)

    total_files = 0
    for target in args.target:
        print(f"🔄 {target}/ を処理中...")
        count = normalizer.normalize_directory(target)
        total_files += count
        if count > 0:
            print(f"   {count}件のファイルを処理")

    # index.json の更新
    print("\n🔄 index.json を処理中...")
    ref_count = normalizer.update_index_json()

    # サマリ出力
    normalizer.report_summary()

    return 0 if (total_files > 0 or ref_count > 0) else 1


if __name__ == "__main__":
    sys.exit(main())
