"""
Ports (抽象インターフェース) for Inbound Forecast Worker
=======================================================
Clean Architecture の Ports & Adapters パターンに従い、
外部依存（DB、ファイルシステム等）を抽象化します。

- InboundActualRepositoryPort: 日次実績データの取得
- ReserveDailyRepositoryPort: 予約データの取得
- ForecastResultRepositoryPort: 予測結果の保存
"""
