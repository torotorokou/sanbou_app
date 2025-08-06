#!/usr/bin/env python3
"""
自動インポート修正スクリプト

相対インポートを絶対インポートに変更し、プロジェクト全体の
インポート構造を統一するためのユーティリティスクリプトです。
"""

import re
from pathlib import Path


def fix_imports_in_file(file_path: Path, project_root: Path):
    """
    単一ファイルのインポート文を修正

    指定されたファイル内の相対インポートを絶対インポートに変更します。

    Args:
        file_path (Path): 修正対象のファイルパス
        project_root (Path): プロジェクトルートディレクトリのパス

    Returns:
        bool: ファイルが変更された場合True、変更されなかった場合False
    """
    try:
        # ファイル内容を読み込み
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content

        # backend_sharedのインポートを修正
        content = re.sub(r"from\s+backend_shared\.", "from backend_shared.", content)

        # app/api/st_app内での相対インポートを修正
        if "app/api/st_app" in str(file_path):
            # from app_pages. -> from app.api.st_app.app_pages.
            content = re.sub(
                r"from\s+app_pages\.", "from app.api.st_app.app_pages.", content
            )

            # from components. -> from app.api.st_app.components.
            content = re.sub(
                r"from\s+components\.", "from app.api.st_app.components.", content
            )

            # from utils. -> from app.api.st_app.utils.
            content = re.sub(r"from\s+utils\.", "from app.api.st_app.utils.", content)

            # from config. -> from app.api.st_app.config.
            content = re.sub(r"from\s+config\.", "from app.api.st_app.config.", content)

            # from logic. -> from app.api.st_app.logic.
            content = re.sub(r"from\s+logic\.", "from app.api.st_app.logic.", content)

        # app/api/services内での相対インポートを修正
        if "app/api/services" in str(file_path):
            # from . import -> from app.api.services.
            content = re.sub(
                r"from\s+\.\s+import", "from app.api.services import", content
            )

        # backend_shared内での相対インポートを修正
        if "backend_shared" in str(file_path):
            content = re.sub(r"from\s+\.", "from backend_shared.", content)

        # 変更があった場合のみファイルを書き換え
        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"修正完了: {file_path}")
            return True

        return False

    except Exception as e:
        print(f"エラー in {file_path}: {e}")
        return False


def main():
    """メイン処理"""
    project_root = Path("/backend")

    # Pythonファイルを検索
    python_files = []
    for pattern in ["**/*.py"]:
        python_files.extend(project_root.glob(pattern))

    # __pycache__ディレクトリのファイルは除外
    python_files = [f for f in python_files if "__pycache__" not in str(f)]

    print(f"対象ファイル数: {len(python_files)}")

    fixed_count = 0
    for py_file in python_files:
        if fix_imports_in_file(py_file, project_root):
            fixed_count += 1

    print(f"修正完了: {fixed_count}ファイル")


if __name__ == "__main__":
    main()
