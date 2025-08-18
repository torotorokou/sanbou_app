"""
Factory撤廃方針。ただし互換用にレジストリを提供。

利用しない構成が推奨だが、どうしてもFactoryが必要な箇所向けに
編集不要の @register デコレータで登録し、get_generator で取得可能とする。
"""

from typing import Callable, Dict, Type

from .base_report_generator import BaseReportGenerator

_REGISTRY: Dict[str, Type[BaseReportGenerator]] = {}


def register(
    key: str,
) -> Callable[[Type[BaseReportGenerator]], Type[BaseReportGenerator]]:
    def _decorator(cls: Type[BaseReportGenerator]) -> Type[BaseReportGenerator]:
        _REGISTRY[key] = cls
        return cls

    return _decorator


def get_generator(key: str) -> Type[BaseReportGenerator]:
    if key not in _REGISTRY:
        raise KeyError(
            f"Generator not registered for key: {key}. Available: {list(_REGISTRY)}"
        )
    return _REGISTRY[key]
