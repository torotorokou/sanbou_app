"""
Backend Shared Domain Exceptions

全バックエンドサービス（core_api, ai_api, ledger_api, rag_api, manual_api等）で
共通利用するドメイン層の例外クラスを定義します。

これにより以下を実現:
- ビジネスロジックとHTTPレスポンスの分離
- 統一されたエラーハンドリング
- 各サービスでの例外クラス重複実装の回避

使用例:
    from backend_shared.core.domain.exceptions import ValidationError, NotFoundError
    
    if not is_valid:
        raise ValidationError("Invalid date range", field="start_date")
    
    if not resource:
        raise NotFoundError("User", user_id)
"""


class DomainException(Exception):
    """
    ドメイン層の基底例外
    
    ビジネスルール違反や不変条件の破綻を表現します。
    全てのドメイン例外はこのクラスを継承します。
    """
    pass


class ValidationError(DomainException):
    """
    バリデーションエラー
    
    入力値が業務ルールに違反している場合に使用します。
    例: 日付範囲が不正、必須項目が空、形式が不正 など
    
    HTTP Status: 400 Bad Request
    """
    def __init__(self, message: str, field: str | None = None):
        """
        Args:
            message: エラーメッセージ
            field: エラーが発生したフィールド名（オプション）
        """
        self.message = message
        self.field = field
        super().__init__(message)


class NotFoundError(DomainException):
    """
    リソースが見つからない
    
    指定されたIDやキーのリソースが存在しない場合に使用します。
    例: アップロードファイルが存在しない、ユーザーが見つからない など
    
    HTTP Status: 404 Not Found
    """
    def __init__(self, entity: str, entity_id: str | int):
        """
        Args:
            entity: エンティティ名（例: "User", "Upload File", "Invoice"）
            entity_id: エンティティの識別子（ID、名前など）
        """
        self.entity = entity
        self.entity_id = entity_id
        self.message = f"{entity} not found: {entity_id}"
        super().__init__(self.message)
    
    # 後方互換性のため
    @property
    def resource_type(self):
        return self.entity
    
    @property
    def identifier(self):
        return self.entity_id


class BusinessRuleViolation(DomainException):
    """
    ビジネスルール違反
    
    業務ロジック上許可されない操作を試みた場合に使用します。
    例: 締め処理後のデータ変更、重複登録の試み など
    
    HTTP Status: 422 Unprocessable Entity
    """
    def __init__(self, rule: str, details: str | None = None):
        """
        Args:
            rule: 違反したビジネスルール
            details: 詳細情報（オプション）
        """
        self.rule = rule
        self.details = details
        message = f"Business rule violated: {rule}"
        if details:
            message += f" ({details})"
        super().__init__(message)


class UnauthorizedError(DomainException):
    """
    認証エラー
    
    認証が必要なリソースに未認証でアクセスした場合に使用します。
    
    HTTP Status: 401 Unauthorized
    """
    def __init__(self, message: str = "Authentication required"):
        self.message = message
        super().__init__(message)


class ForbiddenError(DomainException):
    """
    権限エラー
    
    認証済みだが権限が不足している場合に使用します。
    例: 管理者権限が必要な操作を一般ユーザーが試みた など
    
    HTTP Status: 403 Forbidden
    """
    def __init__(self, message: str = "Access forbidden", required_permission: str | None = None):
        self.message = message
        self.required_permission = required_permission
        super().__init__(message)


class InfrastructureError(Exception):
    """
    インフラストラクチャ層のエラー
    
    外部システム（DB、API、ファイルシステム）との連携で発生するエラー。
    DomainExceptionではなくExceptionを直接継承（技術的エラー）。
    
    HTTP Status: 503 Service Unavailable
    """
    def __init__(self, message: str, cause: Exception | None = None):
        """
        Args:
            message: エラーメッセージ
            cause: 元となった例外（オプション）
        """
        self.message = message
        self.cause = cause
        super().__init__(message)


class ExternalServiceError(InfrastructureError):
    """
    外部サービスエラー
    
    外部API呼び出しでエラーが発生した場合に使用します。
    例: ledger_api, rag_api, manual_apiなどとの通信エラー
    
    HTTP Status: 502 Bad Gateway または 504 Gateway Timeout
    """
    def __init__(
        self, 
        service_name: str, 
        message: str, 
        status_code: int | None = None, 
        cause: Exception | None = None
    ):
        """
        Args:
            service_name: サービス名（例: "ledger_api", "rag_api"）
            message: エラーメッセージ
            status_code: 外部サービスから返されたHTTPステータスコード（オプション）
            cause: 元となった例外（オプション）
        """
        self.service_name = service_name
        self.status_code = status_code
        super().__init__(f"{service_name}: {message}", cause)
