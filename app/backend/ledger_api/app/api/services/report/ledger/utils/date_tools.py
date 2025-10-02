"""Date utility functions wrapper."""
from ._date_tools import (
    get_weekday_japanese as _get_weekday_japanese,
    to_reiwa_format as _to_reiwa_format,
    to_japanese_era as _to_japanese_era,
    to_japanese_month_day as _to_japanese_month_day,
    get_title_from_date as _get_title_from_date,
)


def get_weekday_japanese(d):
    return _get_weekday_japanese(d)


def to_reiwa_format(d):
    return _to_reiwa_format(d)


def to_japanese_era(d):
    return _to_japanese_era(d)


def to_japanese_month_day(d):
    return _to_japanese_month_day(d)


def get_title_from_date(d):
    return _get_title_from_date(d)
