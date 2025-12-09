"""
依存性注入用のファクトリ関数

FastAPIのDependsで使用するサービスインスタンスを生成します。

【フロントエンド開発者向け説明】
この設定により、以下2つのAPIエンドポイントが利用可能です：

1. /test-answer → get_dummy_response_service()
   - 開発・テスト用の高速ダミーAPI
   - AI処理なし、即座にレスポンス
   - フロントエンド開発時のモックデータとして使用

2. /generate-answer → get_ai_response_service() 
   - 本番用のAI回答生成API
   - OpenAI GPT使用、2-5秒の処理時間
   - 実際のユーザー向け機能

両方とも同じレスポンス形式なので、エンドポイントURLを
切り替えるだけで開発→本番移行が可能です。
"""

from app.core.ports.rag.pdf_service_port import PDFServiceBase
from app.core.usecases.rag.dummy_response_service import DummyResponseService
from app.core.usecases.rag.ai_response_service import AIResponseService
from app.core.usecases.manuals.manuals_service import ManualsService
from app.config.di_providers import get_pdf_service as _get_pdf_service
from app.config.di_providers import get_dummy_response_service as _get_dummy_response_service
from app.config.di_providers import get_ai_response_service as _get_ai_response_service
from app.config.di_providers import get_manuals_service as _get_manuals_service


def get_pdf_service() -> PDFServiceBase:
    """PDFサービスのインスタンスを取得"""
    return _get_pdf_service()


def get_dummy_response_service() -> DummyResponseService:
    """ダミーレスポンスサービスのインスタンスを取得"""
    return _get_dummy_response_service()


def get_ai_response_service() -> AIResponseService:
    """AI回答サービスのインスタンスを取得"""
    return _get_ai_response_service()


def get_manuals_service() -> ManualsService:
    """マニュアルサービスのインスタンスを取得"""
    return _get_manuals_service()
