#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
st_app から api への移管状況を検証するスクリプト

このスクリプトは以下を確認します:
1. app/api 内の st_app への依存関係
2. st_app 内の app.api への逆依存関係
3. 移管されていない機能の特定
4. st_app 削除前の最終チェックリスト
"""

import ast
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple


class DependencyAnalyzer:
    """依存関係を分析するクラス"""

    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.api_path = self.root_path / "app" / "api"
        self.st_app_path = self.root_path / "app" / "st_app"

        # 依存関係の記録
        self.api_to_st_app: Dict[str, List[str]] = defaultdict(list)
        self.st_app_to_api: Dict[str, List[str]] = defaultdict(list)

        # 関数・クラスの記録
        self.api_functions: Dict[str, Set[str]] = defaultdict(set)
        self.st_app_functions: Dict[str, Set[str]] = defaultdict(set)

    def analyze_imports(self, file_path: Path) -> Tuple[List[str], List[str]]:
        """ファイルのインポート文を解析"""
        st_app_imports = []
        api_imports = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if "st_app" in alias.name:
                            st_app_imports.append(alias.name)
                        elif "app.api" in alias.name:
                            api_imports.append(alias.name)

                elif isinstance(node, ast.ImportFrom):
                    if node.module and "st_app" in node.module:
                        st_app_imports.append(node.module)
                    elif node.module and "app.api" in node.module:
                        api_imports.append(node.module)

        except Exception as e:
            print(f"Warning: Could not parse {file_path}: {e}")

        return st_app_imports, api_imports

    def extract_definitions(self, file_path: Path) -> Tuple[Set[str], Set[str]]:
        """ファイル内の関数とクラスの定義を抽出"""
        functions = set()
        classes = set()

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.add(node.name)
                elif isinstance(node, ast.ClassDef):
                    classes.add(node.name)

        except Exception as e:
            print(f"Warning: Could not parse {file_path}: {e}")

        return functions, classes

    def scan_directory(self, directory: Path, target: str = "api"):
        """ディレクトリを再帰的にスキャン"""
        for py_file in directory.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue

            relative_path = py_file.relative_to(self.root_path)

            # インポートの分析
            st_app_imports, api_imports = self.analyze_imports(py_file)

            if target == "api" and st_app_imports:
                self.api_to_st_app[str(relative_path)] = st_app_imports
            elif target == "st_app" and api_imports:
                self.st_app_to_api[str(relative_path)] = api_imports

            # 定義の抽出
            functions, classes = self.extract_definitions(py_file)

            if target == "api":
                self.api_functions[str(relative_path)] = functions | classes
            else:
                self.st_app_functions[str(relative_path)] = functions | classes

    def analyze(self):
        """完全な分析を実行"""
        print("=" * 80)
        print("st_app → api 移管状況の分析を開始します")
        print("=" * 80)
        print()

        # APIディレクトリのスキャン
        print("📂 app/api のスキャン中...")
        if self.api_path.exists():
            self.scan_directory(self.api_path, target="api")
        else:
            print(f"⚠️  {self.api_path} が見つかりません")

        # st_appディレクトリのスキャン
        print("📂 app/st_app のスキャン中...")
        if self.st_app_path.exists():
            self.scan_directory(self.st_app_path, target="st_app")
        else:
            print(f"⚠️  {self.st_app_path} が見つかりません")

        print()
        self.print_report()

    def print_report(self):
        """分析結果のレポートを出力"""
        print("=" * 80)
        print("📊 分析結果レポート")
        print("=" * 80)
        print()

        # 1. app/api から st_app への依存
        print("【1】app/api → st_app への依存関係")
        print("-" * 80)
        if self.api_to_st_app:
            print("⚠️  以下のファイルが st_app に依存しています:")
            print()
            for file_path, imports in sorted(self.api_to_st_app.items()):
                print(f"  📄 {file_path}")
                for imp in imports:
                    print(f"     └─ {imp}")
                print()
            print(
                f"❌ 合計 {len(self.api_to_st_app)} ファイルが st_app に依存しています"
            )
        else:
            print("✅ app/api は st_app に依存していません")
        print()

        # 2. st_app から app.api への逆依存
        print("【2】st_app → app.api への逆依存関係")
        print("-" * 80)
        if self.st_app_to_api:
            print("⚠️  以下の st_app ファイルが app.api に依存しています:")
            print()
            for file_path, imports in sorted(self.st_app_to_api.items()):
                print(f"  📄 {file_path}")
                for imp in imports:
                    print(f"     └─ {imp}")
                print()
            print(
                f"❌ 合計 {len(self.st_app_to_api)} ファイルが app.api に依存しています"
            )
            print("   これらのファイルは循環依存を引き起こしています")
        else:
            print("✅ st_app は app.api に依存していません")
        print()

        # 3. 統計情報
        print("【3】統計情報")
        print("-" * 80)
        print(f"app/api 内のファイル数: {len(self.api_functions)}")
        print(f"st_app 内のファイル数: {len(self.st_app_functions)}")

        total_api_defs = sum(len(defs) for defs in self.api_functions.values())
        total_st_app_defs = sum(len(defs) for defs in self.st_app_functions.values())
        print(f"app/api 内の関数/クラス数: {total_api_defs}")
        print(f"st_app 内の関数/クラス数: {total_st_app_defs}")
        print()

        # 4. st_app 削除のチェックリスト
        print("【4】st_app 削除前のチェックリスト")
        print("-" * 80)

        can_delete = True

        if self.api_to_st_app:
            print(
                "❌ app/api が st_app に依存しています → 依存を解消する必要があります"
            )
            can_delete = False
        else:
            print("✅ app/api は st_app に依存していません")

        if self.st_app_to_api:
            print("⚠️  st_app が app.api に逆依存しています → これは許容可能ですが、")
            print("   st_app を削除すると、これらのファイルも使えなくなります")
        else:
            print("✅ st_app は app.api に依存していません")

        print()

        if can_delete:
            print("=" * 80)
            print("✅ st_app を安全に削除できます！")
            print("=" * 80)
        else:
            print("=" * 80)
            print("❌ st_app を削除する前に、上記の依存関係を解消してください")
            print("=" * 80)

        print()

        # 5. 推奨される対応
        print("【5】推奨される対応")
        print("-" * 80)

        if self.api_to_st_app:
            print("以下のファイルの st_app への依存を app/api 内の対応するモジュールに")
            print("置き換える必要があります:")
            print()
            for file_path in sorted(self.api_to_st_app.keys()):
                print(f"  • {file_path}")
            print()

        if self.st_app_to_api:
            print("以下の st_app ファイルは app.api に依存しているため、")
            print("st_app を削除するとエラーになります:")
            print()
            for file_path in sorted(self.st_app_to_api.keys()):
                print(f"  • {file_path}")
            print()
            print("これらのファイルが必要な場合は、app.api への依存を削除するか、")
            print("不要であればそのまま st_app ごと削除してください。")
            print()

        print("=" * 80)


def main():
    """メイン関数"""
    # スクリプトのディレクトリを取得
    script_dir = Path(__file__).parent

    analyzer = DependencyAnalyzer(script_dir)
    analyzer.analyze()


if __name__ == "__main__":
    main()
