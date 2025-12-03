from __future__ import annotations
import argparse
from datetime import date
from backend_shared.application.logging import get_module_logger as get_logger
from app.infra.db.pg_repositories import PgActualsRepository, PgRatiosRepository
from app.core.usecases.rebuild_daytype_ratios import rebuild_daytype_ratios

logger = get_logger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Rebuild daytype ratios.")
    parser.add_argument("--effective-from", required=True, help="YYYY-MM-01（月初日）例: 2025-11-01")
    parser.add_argument("--dry-run", action="store_true", help="保存せず算出のみ（ログ出力）")
    args = parser.parse_args()

    y, m, d = map(int, args.effective_from.split("-"))
    eff = date(y, m, d)

    actuals_repo = PgActualsRepository()
    ratios_repo  = PgRatiosRepository()

    if args.dry_run:
        # ユースケース内部の保存呼び出しを避けたい場合は、別ユースケースに分けてもよい
        # 簡易にはそのまま実行し、RatiosRepoをダミー実装に差し替えるのもあり
        logger.info("[DRY RUN] start")
        rebuild_daytype_ratios(eff, actuals_repo, ratios_repo)  # 実装を分けるならここを変更
        logger.info("[DRY RUN] end")
    else:
        rebuild_daytype_ratios(eff, actuals_repo, ratios_repo)

if __name__ == "__main__":
    main()
