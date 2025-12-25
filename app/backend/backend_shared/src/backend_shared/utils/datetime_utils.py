"""
Datetime Utilities - 日付時刻ユーティリティモジュール

【概要】
アプリケーション全体で統一されたタイムゾーン処理を提供します。
環境変数でタイムゾーンを設定可能で、デフォルトは Asia/Tokyo です。

【主な機能】
1. アプリケーションタイムゾーンの取得（キャッシュ済み）
2. 現在時刻の取得（アプリケーションタイムゾーン）
3. datetime のタイムゾーン変換
4. 日本語形式でのフォーマット

【設計方針】
- ZoneInfo オブジェクトをキャッシュしてパフォーマンスを最適化
- 環境変数 APP_TIMEZONE でタイムゾーンを設定可能
- 日本語フォーマット関数を提供（ビジネスロジックで頻出）

【使用例】
```python
from backend_shared.utils.datetime_utils import (
    now_in_app_timezone,
    format_datetime_jp
)

# 現在時刻を取得してフォーマット
timestamp = format_datetime_jp(now_in_app_timezone())
print(timestamp)  # '2024年12月04日 15:30'
```
"""

import os
from datetime import date, datetime, timezone
from functools import lru_cache
from zoneinfo import ZoneInfo


@lru_cache(maxsize=1)
def get_app_timezone() -> ZoneInfo:
    """
    アプリケーションのタイムゾーンを取得（キャッシュ済み）

    環境変数 APP_TIMEZONE で設定可能（デフォルト: Asia/Tokyo）
    一度取得した ZoneInfo オブジェクトをキャッシュするため、
    繰り返し呼び出してもパフォーマンスに影響しません。

    Returns:
        ZoneInfo: アプリケーションのタイムゾーン

    Examples:
        >>> tz = get_app_timezone()
        >>> tz
        ZoneInfo(key='Asia/Tokyo')

        >>> # 環境変数で変更可能
        >>> os.environ["APP_TIMEZONE"] = "UTC"
        >>> get_app_timezone.cache_clear()  # キャッシュクリア
        >>> tz = get_app_timezone()
        >>> tz
        ZoneInfo(key='UTC')
    """
    tz_name = os.getenv("APP_TIMEZONE", "Asia/Tokyo")
    return ZoneInfo(tz_name)


def now_in_app_timezone() -> datetime:
    """
    アプリケーションタイムゾーンでの現在時刻を取得

    タイムゾーン情報付きの datetime オブジェクトを返します。

    Returns:
        datetime: タイムゾーン付き現在時刻

    Examples:
        >>> now = now_in_app_timezone()
        >>> now.tzinfo
        ZoneInfo(key='Asia/Tokyo')

        >>> # タイムゾーン付きで返されるため、そのまま比較可能
        >>> from datetime import timedelta
        >>> one_hour_ago = now - timedelta(hours=1)
        >>> one_hour_ago < now
        True
    """
    return datetime.now(get_app_timezone())


def to_app_timezone(dt: datetime) -> datetime:
    """
    datetime オブジェクトをアプリケーションタイムゾーンに変換

    naive datetime（タイムゾーン情報なし）の場合は、
    アプリケーションタイムゾーンを付与します。
    aware datetime（タイムゾーン情報あり）の場合は、
    アプリケーションタイムゾーンに変換します。

    Args:
        dt: 変換元の datetime（naive または aware）

    Returns:
        datetime: アプリケーションタイムゾーンに変換された datetime

    Examples:
        >>> # UTC時刻を JST に変換
        >>> utc_time = datetime(2024, 12, 4, 6, 30, tzinfo=timezone.utc)
        >>> jst_time = to_app_timezone(utc_time)
        >>> jst_time.hour
        15  # JST は UTC+9

        >>> # naive datetime にタイムゾーンを付与
        >>> naive_time = datetime(2024, 12, 4, 15, 30)
        >>> aware_time = to_app_timezone(naive_time)
        >>> aware_time.tzinfo
        ZoneInfo(key='Asia/Tokyo')
    """
    if dt.tzinfo is None:
        # naive datetime の場合はタイムゾーンを付与
        return dt.replace(tzinfo=get_app_timezone())
    else:
        # aware datetime の場合はタイムゾーン変換
        return dt.astimezone(get_app_timezone())


def format_datetime_jp(dt: datetime) -> str:
    """
    datetime を日本語形式にフォーマット

    '年月日 時:分' の形式で出力します。
    タイムゾーン情報がない場合は、そのままフォーマットします。
    タイムゾーン情報がある場合は、アプリケーションタイムゾーンに変換してからフォーマットします。

    Args:
        dt: フォーマット対象の datetime

    Returns:
        str: '2024年12月04日 15:30' 形式の文字列

    Examples:
        >>> now = now_in_app_timezone()
        >>> format_datetime_jp(now)
        '2024年12月04日 15:30'

        >>> # タイムゾーン変換してからフォーマット
        >>> utc_time = datetime(2024, 12, 4, 6, 30, tzinfo=timezone.utc)
        >>> format_datetime_jp(utc_time)
        '2024年12月04日 15:30'  # JST に変換されている
    """
    if dt.tzinfo is not None:
        dt = to_app_timezone(dt)
    return dt.strftime("%Y年%m月%d日 %H:%M")


def format_date_jp(d: date) -> str:
    """
    date を日本語形式にフォーマット

    '年月日' の形式で出力します。

    Args:
        d: フォーマット対象の date

    Returns:
        str: '2024年12月04日' 形式の文字列

    Examples:
        >>> today = date.today()
        >>> format_date_jp(today)
        '2024年12月04日'

        >>> # datetime から date を取り出してフォーマット
        >>> now = now_in_app_timezone()
        >>> format_date_jp(now.date())
        '2024年12月04日'
    """
    return d.strftime("%Y年%m月%d日")


def format_datetime_iso(dt: datetime) -> str:
    """
    datetime を ISO 8601 形式にフォーマット

    API レスポンスなど、標準的な形式が必要な場合に使用します。
    タイムゾーン情報を含む形式で出力します。

    Args:
        dt: フォーマット対象の datetime

    Returns:
        str: '2024-12-04T15:30:00+09:00' 形式の文字列

    Examples:
        >>> now = now_in_app_timezone()
        >>> format_datetime_iso(now)
        '2024-12-04T15:30:00+09:00'
    """
    if dt.tzinfo is not None:
        dt = to_app_timezone(dt)
    return dt.isoformat()


def parse_datetime_iso(iso_string: str) -> datetime:
    """
    ISO 8601 形式の文字列を datetime に変換

    API リクエストなどで受け取った ISO 形式の文字列をパースします。

    Args:
        iso_string: ISO 8601 形式の文字列

    Returns:
        datetime: パースされた datetime（アプリケーションタイムゾーン）

    Raises:
        ValueError: 不正な形式の文字列

    Examples:
        >>> dt = parse_datetime_iso('2024-12-04T15:30:00+09:00')
        >>> dt.hour
        15

        >>> # UTC で受け取った場合も JST に変換
        >>> dt = parse_datetime_iso('2024-12-04T06:30:00Z')
        >>> dt.hour
        15  # JST に変換されている
    """
    dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
    return to_app_timezone(dt)


__all__ = [
    "get_app_timezone",
    "now_in_app_timezone",
    "to_app_timezone",
    "format_datetime_jp",
    "format_date_jp",
    "format_datetime_iso",
    "parse_datetime_iso",
]
