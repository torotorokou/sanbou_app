"""
Local File Storage Repository

ローカルファイルシステム用の FileStoragePort 実装。
"""
from pathlib import Path
from typing import List


class LocalFileStorageRepository:
    """ローカルファイルストレージリポジトリ
    
    ローカルファイルシステムに対する FileStoragePort の具体実装。
    開発環境やテスト環境で使用することを想定。
    """

    def __init__(self, base_dir: Path) -> None:
        """初期化
        
        Args:
            base_dir: ベースディレクトリ（全ての相対パスの起点）
        """
        self._base_dir = base_dir
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def _full_path(self, path: str) -> Path:
        """相対パスからフルパスを生成
        
        Args:
            path: ベースディレクトリ基準の相対パス
            
        Returns:
            フルパス
        """
        return self._base_dir / path.lstrip("/")

    def read_bytes(self, path: str) -> bytes:
        """指定パスのファイルをバイナリで読み込む"""
        full_path = self._full_path(path)
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        return full_path.read_bytes()

    def read_text(self, path: str, encoding: str = "utf-8") -> str:
        """指定パスのファイルをテキストで読み込む"""
        full_path = self._full_path(path)
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        return full_path.read_text(encoding=encoding)

    def exists(self, path: str) -> bool:
        """指定パスの存在確認"""
        return self._full_path(path).exists()

    def list_files(self, prefix: str) -> List[str]:
        """プレフィックス配下のファイル一覧を取得
        
        ディレクトリのみの場合は空リストを返す。
        """
        full_prefix = self._base_dir / prefix.lstrip("/")
        if not full_prefix.exists():
            return []
        
        result: List[str] = []
        for p in full_prefix.rglob("*"):
            if p.is_file():
                rel_path = str(p.relative_to(self._base_dir))
                result.append(rel_path)
        
        return sorted(result)

    def write_bytes(self, path: str, content: bytes) -> None:
        """指定パスにバイナリデータを書き込む"""
        full_path = self._full_path(path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(content)

    def write_text(self, path: str, content: str, encoding: str = "utf-8") -> None:
        """指定パスにテキストデータを書き込む"""
        full_path = self._full_path(path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding=encoding)
