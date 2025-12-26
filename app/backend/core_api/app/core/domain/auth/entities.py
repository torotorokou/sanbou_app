"""
Auth Domain Entities - 認証ドメインエンティティ

【概要】
認証済みユーザーを表現する不変オブジェクト。

【設計方針】
- dataclass(frozen=True) で不変性を保証
- 認証方式に依存しない抽象的なユーザー表現
- 最小限の情報のみを保持（email, display_name）
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class AuthUser:
    """
    認証済みユーザーエンティティ

    認証プロバイダ（Dev / IAP / OAuth2 等）から返される
    ユーザー情報を統一的に扱うための不変オブジェクト。

    Attributes:
        email: ユーザーのメールアドレス（必須、一意識別子）
        display_name: 表示名（オプション、UI表示用）
        user_id: ユーザーID（オプション、システム内部識別子）
        role: ユーザーロール（オプション、権限管理用）

    Examples:
        >>> user = AuthUser(
        ...     email="user@honest-recycle.co.jp",
        ...     display_name="山田太郎",
        ...     user_id="user_12345",
        ...     role="admin"
        ... )
        >>> user.email
        'user@honest-recycle.co.jp'
    """

    email: str
    display_name: str | None = None
    user_id: str | None = None
    role: str | None = None
