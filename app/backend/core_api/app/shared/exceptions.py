"""
Shared Exceptions - アプリケーション全体で共通のカスタム例外

ドメイン層・アプリケーション層で使用する例外クラスを定義します。
これにより、ビジネスロジックと HTTP レスポンスの分離が可能になります。
"""


class DomainException(Exception):
    """
    ドメイン層の基底例外
    
    ビジネスルール違反や不変条件の破綻を表現します。
    """
    pass


class ValidationError(DomainException):
    """
    バリデーションエラー
    
    入力値が業務ルールに違反している場合に使用します。
    例: 日付範囲が不正、必須項目が空、形式が不正 など
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
    """
    def __init__(self, resource_type: str, identifier: str | int):
        """
        Args:
            resource_type: リソースの種類（例: "Upload File", "User"）
            identifier: リソースの識別子（ID、名前など）
        """
        self.resource_type = resource_type
        self.identifier = identifier
        self.message = f"{resource_type} not found: {identifier}"
        super().__init__(self.message)


class BusinessRuleViolation(DomainException):
    """
    ビジネスルール違反
    
    業務ロジック上許可されない操作を試みた場合に使用します。
    例: 締め処理後のデータ変更、重複登録の試み など
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


class InfrastructureError(Exception):
    """
    インフラストラクチャ層のエラー
    
    外部システム（DB、API、ファイルシステム）との連携で発生するエラー。
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
