#!/usr/bin/env python3
"""
check_todos.py - TODO/FIXME コメントをチェック

pre-push 時に実行され、TODO や FIXME コメントが含まれている場合に警告を出します。
（実際にはブロックせず、情報提供のみ）
"""
import sys
import re


def check_todos(filenames):
    """
    ファイル内の TODO/FIXME コメントをチェック

    Args:
        filenames: チェック対象のファイルパスのリスト

    Returns:
        0: 問題なし, 1: TODOが見つかった
    """
    todo_pattern = re.compile(r'#\s*(TODO|FIXME|XXX|HACK)', re.IGNORECASE)
    found_todos = []

    for filename in filenames:
        try:
            with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, start=1):
                    if todo_pattern.search(line):
                        found_todos.append(f"{filename}:{line_num}: {line.strip()}")
        except Exception as e:
            print(f"⚠️  警告: {filename} の読み込み中にエラー: {e}", file=sys.stderr)
            continue

    if found_todos:
        print("📝 情報: 以下のファイルに TODO/FIXME コメントが含まれています:")
        for todo in found_todos[:10]:  # 最大10件まで表示
            print(f"  {todo}")
        if len(found_todos) > 10:
            print(f"  ... 他 {len(found_todos) - 10} 件")
        print("\n🚀 問題ありません。push を続行します。")
        # 情報提供のみなので終了コード 0
        return 0

    return 0


def main():
    """メインエントリーポイント"""
    if len(sys.argv) < 2:
        # ファイルが渡されない場合は何もしない
        return 0

    filenames = sys.argv[1:]
    return check_todos(filenames)


if __name__ == '__main__':
    sys.exit(main())
