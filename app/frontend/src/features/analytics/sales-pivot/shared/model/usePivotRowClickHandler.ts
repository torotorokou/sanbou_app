/**
 * features/analytics/sales-pivot/shared/model/usePivotRowClickHandler.ts
 * Pivot行クリック時のハンドラー
 */

import { useCallback } from "react";
import type { Mode, MetricEntry, GroupBy } from "./types";
import type { DrawerState } from "./usePivotDrawerState";
import { logger } from "@/shared";

interface PivotRowClickHandlerParams {
  drawer: DrawerState;
  openDetailDrawer: (
    lastGroupBy: GroupBy,
    repId?: string,
    customerId?: string,
    itemId?: string,
    dateValue?: string,
    title?: string,
  ) => Promise<void>;
}

export function usePivotRowClickHandler(params: PivotRowClickHandlerParams) {
  const { drawer, openDetailDrawer } = params;

  const handlePivotRowClick = useCallback(
    async (row: MetricEntry, axis: Mode) => {
      if (!drawer.open) return;

      // 現在のDrawer状態から必要な情報を取得
      const { baseAxis, baseId, repIds } = drawer;

      // 集計パスの構築: baseAxis → activeAxis → クリックした行の軸
      // 例: 顧客(base) → 品名(active) → 行をクリック
      // lastGroupBy = activeAxis (クリックされたタブの軸)
      const lastGroupBy = axis as GroupBy;

      // フィルタ条件を構築
      const repId = repIds[0]; // 最初の営業IDを使用
      let customerId: string | undefined;
      let itemId: string | undefined;
      let dateValue: string | undefined;

      // baseAxisに応じてフィルタを設定
      if (baseAxis === "customer") {
        customerId = baseId;
      } else if (baseAxis === "item") {
        itemId = baseId;
      } else if (baseAxis === "date") {
        dateValue = baseId;
      }

      // activeAxis（クリックされた行の軸）に応じてフィルタを追加
      if (axis === "customer") {
        customerId = row.id;
      } else if (axis === "item") {
        itemId = row.id;
      } else if (axis === "date") {
        dateValue = row.id;
      }

      logger.log("🔍 Pivot行クリック:", {
        baseAxis,
        baseId,
        clickedAxis: axis,
        clickedRow: { id: row.id, name: row.name },
        lastGroupBy,
        filters: { repId, customerId, itemId, dateValue },
      });

      // タイトル構築
      const title = `${row.name} の詳細明細`;

      await openDetailDrawer(
        lastGroupBy,
        repId,
        customerId,
        itemId,
        dateValue,
        title,
      );
    },
    [drawer, openDetailDrawer],
  );

  return { handlePivotRowClick };
}
