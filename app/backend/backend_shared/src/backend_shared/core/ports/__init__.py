"""
Ports Layer

UseCase が依存する抽象インターフェース定義。
- Repository: データ永続化の抽象
- Gateway: 外部サービス連携の抽象
- FileStoragePort: ファイルストレージの抽象
- その他のポート定義
"""
from .file_storage_port import FileStoragePort

__all__ = [
    "FileStoragePort",
]
