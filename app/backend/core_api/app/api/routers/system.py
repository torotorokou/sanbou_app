"""
System Router

システム関連のエンドポイント（ヘルスチェック、ストレージ状態確認など）
"""
from fastapi import APIRouter, Depends, Query
from typing import Dict, Any

from backend_shared.core.ports.file_storage_port import FileStoragePort
from app.config.di_providers import get_file_storage
from app.core.usecases.system.check_storage_health_uc import CheckStorageHealthUseCase

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/storage/health")
def check_storage_health(
    test_prefix: str = Query(default="", description="テスト対象のプレフィックス"),
    storage: FileStoragePort = Depends(get_file_storage),
) -> Dict[str, Any]:
    """ストレージヘルスチェック
    
    FileStoragePort を使用して、ストレージへの接続と基本的な操作が
    正常に動作することを確認します。
    
    Args:
        test_prefix: テスト対象のプレフィックス（省略時はルート）
        storage: ストレージポート（DIで注入）
    
    Returns:
        ヘルスチェック結果
    """
    usecase = CheckStorageHealthUseCase(storage=storage)
    return usecase.execute(test_prefix=test_prefix)
