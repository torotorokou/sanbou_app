# -*- coding: utf-8 -*-
"""
SQL識別子定数

データベーステーブル名、ビュー名、スキーマ名を一元管理する定数ファイル。

目的:
  - SQL文字列のハードコードを防ぎ、保守性を向上
  - テーブル名変更時の影響範囲を最小化
  - IDEの自動補完とリファクタリング機能を活用

使用例:
    from app.infra.db.sql_names import V_RECEIVE_DAILY, V_CALENDAR
    
    sql = f'''
    SELECT * FROM {V_RECEIVE_DAILY}
    WHERE ddate >= :start
    '''

注意:
  - 値はバインドパラメータではなく、SQL識別子として使用する
  - f-stringで直接埋め込み(識別子はプレースホルダにできない)
"""

# martスキーマのビュー(集約済みデータ)
V_RECEIVE_DAILY   = "mart.v_receive_daily"    # 日次搬入集計ビュー
V_RECEIVE_WEEKLY  = "mart.v_receive_weekly"   # 週次搬入集計ビュー
V_RECEIVE_MONTHLY = "mart.v_receive_monthly"  # 月次搬入集計ビュー

# refスキーマのビュー(参照データ)
V_CALENDAR = "ref.v_calendar_classified"  # カレンダービュー(営業日区分付き)