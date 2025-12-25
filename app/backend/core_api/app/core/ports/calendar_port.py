"""
Calendar Query Port - カレンダーデータ取得の抽象インターフェース

営業カレンダーデータ（営業日判定・祝日情報など）を取得するための Port。
"""

from typing import Any, Protocol


class ICalendarQuery(Protocol):
    """
    カレンダーデータ取得の抽象インターフェース

    実装クラスは ref.v_calendar_classified ビューまたは
    同等のデータソースからカレンダー情報を取得します。
    """

    def get_month_calendar(self, year: int, month: int) -> list[dict[str, Any]]:
        """
        指定された年月のカレンダーデータを取得

        Args:
            year: 年 (1900-2100)
            month: 月 (1-12)

        Returns:
            カレンダーデータのリスト。各要素は以下のキーを含む辞書:
            - ddate: 日付
            - y: 年
            - m: 月
            - iso_year: ISO年
            - iso_week: ISO週番号
            - iso_dow: ISO曜日 (1=月曜, 7=日曜)
            - is_holiday: 祝日フラグ
            - is_second_sunday: 第2日曜日フラグ
            - is_company_closed: 会社休業日フラグ
            - day_type: 日種別 (business, holiday, etc.)
            - is_business: 営業日フラグ

        Raises:
            Exception: データベースエラーまたはクエリ実行エラー
        """
        ...
