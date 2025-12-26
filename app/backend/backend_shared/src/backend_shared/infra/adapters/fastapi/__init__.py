"""
共通APIモジュール
"""

from .error_handlers import (
    DomainError,
    handle_domain_error,
    handle_unexpected,
    register_error_handlers,
)


__all__ = [
    "DomainError",
    "handle_domain_error",
    "handle_unexpected",
    "register_error_handlers",
]
