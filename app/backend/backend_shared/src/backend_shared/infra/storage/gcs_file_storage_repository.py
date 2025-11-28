"""
GCS File Storage Repository

Google Cloud Storage 用の FileStoragePort 実装。
"""
from typing import List, Optional

try:
    from google.cloud import storage
    from google.cloud.exceptions import NotFound
    _GCS_AVAILABLE = True
except ImportError:
    _GCS_AVAILABLE = False


class GcsFileStorageRepository:
    """GCS ファイルストレージリポジトリ
    
    Google Cloud Storage に対する FileStoragePort の具体実装。
    本番環境や Staging 環境で使用することを想定。
    
    Note:
        google-cloud-storage パッケージが必要です。
        インストールされていない場合は初期化時にエラーを発生させます。
    """

    def __init__(
        self,
        bucket_name: str,
        base_prefix: str = "",
        credentials_path: Optional[str] = None,
    ) -> None:
        """初期化
        
        Args:
            bucket_name: GCS バケット名（gs:// プレフィックスは不要）
            base_prefix: バケット内のベースプレフィックス（省略可）
            credentials_path: サービスアカウントキーのパス（省略時は環境変数から取得）
            
        Raises:
            ImportError: google-cloud-storage がインストールされていない場合
        """
        if not _GCS_AVAILABLE:
            raise ImportError(
                "google-cloud-storage is not installed. "
                "Install it with: pip install google-cloud-storage"
            )
        
        if credentials_path:
            self._client = storage.Client.from_service_account_json(credentials_path)
        else:
            # GOOGLE_APPLICATION_CREDENTIALS 環境変数から自動取得
            self._client = storage.Client()
        
        self._bucket = self._client.bucket(bucket_name)
        self._base_prefix = base_prefix.strip("/")

    def _full_path(self, path: str) -> str:
        """相対パスからフルパスを生成
        
        Args:
            path: ベースプレフィックス基準の相対パス
            
        Returns:
            バケット内のフルパス
        """
        path = path.lstrip("/")
        if self._base_prefix:
            return f"{self._base_prefix}/{path}"
        return path

    def read_bytes(self, path: str) -> bytes:
        """指定パスのファイルをバイナリで読み込む"""
        blob = self._bucket.blob(self._full_path(path))
        try:
            return blob.download_as_bytes()
        except NotFound:
            raise FileNotFoundError(f"File not found in GCS: {path}")

    def read_text(self, path: str, encoding: str = "utf-8") -> str:
        """指定パスのファイルをテキストで読み込む"""
        blob = self._bucket.blob(self._full_path(path))
        try:
            data = blob.download_as_bytes()
            return data.decode(encoding)
        except NotFound:
            raise FileNotFoundError(f"File not found in GCS: {path}")

    def exists(self, path: str) -> bool:
        """指定パスの存在確認"""
        blob = self._bucket.blob(self._full_path(path))
        return blob.exists()

    def list_files(self, prefix: str) -> List[str]:
        """プレフィックス配下のファイル一覧を取得
        
        ディレクトリのみの場合は空リストを返す。
        """
        full_prefix = self._full_path(prefix)
        blobs = self._client.list_blobs(self._bucket, prefix=full_prefix)
        
        result: List[str] = []
        base_len = len(self._base_prefix) + 1 if self._base_prefix else 0
        
        for blob in blobs:
            # ディレクトリマーカー（末尾が/のもの）はスキップ
            if blob.name.endswith("/"):
                continue
            
            # ベースプレフィックスを除去して相対パスを取得
            name = blob.name
            if self._base_prefix and name.startswith(self._base_prefix + "/"):
                name = name[base_len:]
            result.append(name)
        
        return sorted(result)

    def write_bytes(self, path: str, content: bytes) -> None:
        """指定パスにバイナリデータを書き込む"""
        blob = self._bucket.blob(self._full_path(path))
        blob.upload_from_string(content)

    def write_text(self, path: str, content: str, encoding: str = "utf-8") -> None:
        """指定パスにテキストデータを書き込む"""
        blob = self._bucket.blob(self._full_path(path))
        blob.upload_from_string(content, content_type="text/plain")
