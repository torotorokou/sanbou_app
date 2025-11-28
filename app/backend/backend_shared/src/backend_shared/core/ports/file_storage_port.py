"""
File Storage Port

ファイルストレージ抽象ポート（ローカル / GCS 両対応）
Clean Architecture の境界を定義する。
"""
from typing import Protocol, List


class FileStoragePort(Protocol):
    """ファイルストレージ抽象ポート
    
    ローカルファイルシステムと GCS の両方に対応可能な抽象インターフェース。
    UseCase 層はこのインターフェースのみに依存し、具体的な実装には依存しない。
    """

    def read_bytes(self, path: str) -> bytes:
        """指定パスのファイルをバイナリで読み込む
        
        Args:
            path: ファイルパス（ベースディレクトリまたはバケット基準の相対パス）
            
        Returns:
            ファイルの内容（バイト列）
            
        Raises:
            FileNotFoundError: ファイルが存在しない場合
            PermissionError: 読み取り権限がない場合
            Exception: その他のストレージエラー
        """
        ...

    def read_text(self, path: str, encoding: str = "utf-8") -> str:
        """指定パスのファイルをテキストで読み込む
        
        Args:
            path: ファイルパス（ベースディレクトリまたはバケット基準の相対パス）
            encoding: 文字エンコーディング（デフォルト: utf-8）
            
        Returns:
            ファイルの内容（文字列）
            
        Raises:
            FileNotFoundError: ファイルが存在しない場合
            UnicodeDecodeError: エンコーディングエラー
            Exception: その他のストレージエラー
        """
        ...

    def exists(self, path: str) -> bool:
        """指定パスの存在確認
        
        Args:
            path: ファイルパス（ベースディレクトリまたはバケット基準の相対パス）
            
        Returns:
            ファイルが存在する場合 True、存在しない場合 False
        """
        ...

    def list_files(self, prefix: str) -> List[str]:
        """プレフィックス配下のファイル一覧を取得
        
        Args:
            prefix: ファイルパスのプレフィックス
            
        Returns:
            ファイルパスのリスト（ベースディレクトリまたはバケット基準の相対パス）
        """
        ...

    def write_bytes(self, path: str, content: bytes) -> None:
        """指定パスにバイナリデータを書き込む
        
        Args:
            path: ファイルパス（ベースディレクトリまたはバケット基準の相対パス）
            content: 書き込む内容（バイト列）
            
        Raises:
            PermissionError: 書き込み権限がない場合
            Exception: その他のストレージエラー
        """
        ...

    def write_text(self, path: str, content: str, encoding: str = "utf-8") -> None:
        """指定パスにテキストデータを書き込む
        
        Args:
            path: ファイルパス（ベースディレクトリまたはバケット基準の相対パス）
            content: 書き込む内容（文字列）
            encoding: 文字エンコーディング（デフォルト: utf-8）
            
        Raises:
            PermissionError: 書き込み権限がない場合
            Exception: その他のストレージエラー
        """
        ...
