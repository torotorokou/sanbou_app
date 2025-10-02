# services.report.ledger

帳簿（工場日報・搬出入・平均表・管理表）の実装を集約するサービス層です。

 エントリポイント: `average_sheet.py`, `balance_sheet.py`, `factory_report.py`, `management_sheet.py`
 実装詳細は processors/utils に段階的に移行します
 既存の `app/st_app/logic/manage` は後方互換のため当面残しますが、順次撤去予定です

## 使い方（コード内）

```python
 from app.api.services.report.ledger.factory_report import process as process_factory
from app.api.services.report.ledger.balance_sheet import process as process_balance
from app.api.services.report.ledger.average_sheet import process as process_average
from app.api.services.report.ledger.management_sheet import process as process_management
```

## 設計ポリシー


## 変更履歴（移行）

- 2025-10-02: factory_report / average_sheet / management_sheet のエントリをフル実装化
	- st_app 依存のラッパーを廃止し、services側processors/utilsを使用
	- factory_report: shobun/yuuka/yard/summary/make_cell_num/make_label/etcを移植
	- average_sheet: processorsに分割（集計/日付/丸め/tikan）
	- management_sheet: 各帳票の取り込み、スクラップ・選別、日付差し込みを移植
