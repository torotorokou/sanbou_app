"""
Infrastructure layer (インフラストラクチャ層).

外部技術への依存を含む実装を提供します：
- adapters/: Port の具体的な実装
- frameworks/: フレームワーク固有の設定（DB セッション等）

👶 このパッケージの中のコードだけが、pandas, openpyxl, GCS SDK などに直接触れます。
"""
