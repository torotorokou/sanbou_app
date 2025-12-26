#!/usr/bin/env python3
"""
noop_example.py - 何もしないダミーチェックスクリプト

repo: local の構造を示すためのサンプルです。
実際のチェックでは何も行わず、常に成功を返します。
"""
import sys


def main():
    """
    メインエントリーポイント

    Returns:
        0: 常に成功
    """
    # print("✅ noop_example: チェック成功（何もしていません）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
