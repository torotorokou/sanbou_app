"""
Storage Health Check UseCase

ストレージ接続の健全性をチェックするユースケース。
"""
from typing import Dict, Any
from backend_shared.core.ports.file_storage_port import FileStoragePort


class CheckStorageHealthUseCase:
    """ストレージヘルスチェックユースケース
    
    FileStoragePort を使用して、ストレージへの接続と基本的な操作が
    正常に動作することを確認する。
    """

    def __init__(self, storage: FileStoragePort) -> None:
        """初期化
        
        Args:
            storage: ストレージポート
        """
        self._storage = storage

    def execute(self, test_prefix: str = "") -> Dict[str, Any]:
        """ヘルスチェックを実行
        
        Args:
            test_prefix: テスト対象のプレフィックス（省略時はルート）
            
        Returns:
            ヘルスチェック結果
            {
                "status": "ok" | "error",
                "storage_type": "local" | "gcs",
                "test_prefix": str,
                "can_list": bool,
                "file_count": int (if can_list),
                "error": str (if status=error)
            }
        """
        result: Dict[str, Any] = {
            "status": "ok",
            "storage_type": self._get_storage_type(),
            "test_prefix": test_prefix or "(root)",
        }

        try:
            # ファイル一覧取得テスト
            files = self._storage.list_files(test_prefix)
            result["can_list"] = True
            result["file_count"] = len(files)
            
            # ファイルが存在する場合、最初のファイルの存在確認テスト
            if files:
                first_file = files[0]
                exists = self._storage.exists(first_file)
                result["first_file"] = first_file
                result["first_file_exists"] = exists
            
        except Exception as e:
            result["status"] = "error"
            result["can_list"] = False
            result["error"] = str(e)

        return result

    def _get_storage_type(self) -> str:
        """ストレージタイプを推定
        
        Returns:
            "local" | "gcs" | "unknown"
        """
        storage_class_name = type(self._storage).__name__
        if "Local" in storage_class_name:
            return "local"
        elif "Gcs" in storage_class_name or "GCS" in storage_class_name:
            return "gcs"
        else:
            return "unknown"
