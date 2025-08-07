# -*- coding: utf-8 -*-
"""
ブロック単価計算処理（Streamlit用）

このファイルは動的インポート対応のため、streamlit版の実装への参照を提供します。
実際の処理は block_unit_price_streamlit.py に実装されています。
"""

# Streamlit版の実装をインポート
from app.api.st_app.logic.manage.block_unit_price_streamlit import process

# 動的インポートで使用される process 関数をエクスポート
__all__ = ["process"]
