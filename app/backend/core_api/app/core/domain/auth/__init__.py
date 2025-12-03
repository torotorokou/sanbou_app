"""
Auth Domain - 認証・認可ドメインモデル

【概要】
認証済みユーザーを表現するエンティティを定義します。

【主なエンティティ】
- AuthUser: 認証済みユーザー情報（不変オブジェクト）
"""

from .entities import AuthUser

__all__ = ["AuthUser"]
