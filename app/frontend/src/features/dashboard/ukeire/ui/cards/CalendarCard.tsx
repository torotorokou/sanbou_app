/**
 * CalendarCard Component
 * 営業カレンダーを表示するカード（API駆動版）
 */

import React, { useMemo } from "react";
import { Card, Typography, Tooltip, Skeleton } from "antd";
import { InfoCircleOutlined } from "@ant-design/icons";
// dayjs not needed in this card now
import BusinessCalendar from "../components/BusinessCalendar";
import { useUkeireCalendarVM } from "../../application/useUkeireCalendarVM";
import { MockCalendarRepository } from "../../application/adapters/mockCalendar.repository";
// import { HttpCalendarRepository } from "../../application/adapters/httpCalendar.repository";

export type CalendarCardProps = {
  month: string; // YYYY-MM (parent dashboard provides)
  style?: React.CSSProperties;
};

export const CalendarCard: React.FC<CalendarCardProps> = ({ month, style }) => {
  // Repository を DI（開発中は Mock、本番は HTTP に切り替え）
  const repository = useMemo(() => new MockCalendarRepository(), []);
  // const repository = useMemo(() => new HttpCalendarRepository(), []);
  
  // vm follows the month provided by parent (dashboard)
  const vm = useUkeireCalendarVM(repository, month);

  if (vm.loading) {
    return (
      <Card
        bordered
        size="small"
        style={{ height: "100%", display: "flex", flexDirection: "column", ...(style || {}) }}
        bodyStyle={{ display: "flex", flexDirection: "column", padding: 12, gap: 8, flex: 1, minHeight: 0 }}
      >
        <Skeleton active paragraph={{ rows: 6 }} />
      </Card>
    );
  }

  if (vm.error) {
    return (
      <Card
        bordered
        size="small"
        style={{ height: "100%", display: "flex", flexDirection: "column", ...(style || {}) }}
        bodyStyle={{ display: "flex", flexDirection: "column", padding: 12, gap: 8, flex: 1, minHeight: 0 }}
      >
        <Typography.Text type="danger">{vm.error}</Typography.Text>
      </Card>
    );
  }


  return (
    <Card
      bordered
      size="small"
      style={{ height: "100%", display: "flex", flexDirection: "column", ...(style || {}) }}
      bodyStyle={{ display: "flex", flexDirection: "column", padding: 12, gap: 8, flex: 1, minHeight: 0 }}
    >
  <div style={{ display: "flex", justifyContent: "center", alignItems: "center", position: "relative" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <Typography.Title level={5} style={{ margin: 0, fontSize: 16 }}>
            営業カレンダー
          </Typography.Title>
          <Tooltip title="SQL起点のカレンダーデータ。祝日・休業日はサーバ側で管理。">
            <InfoCircleOutlined style={{ color: "#8c8c8c" }} />
          </Tooltip>
        </div>

  {/* right placeholder kept for symmetry if needed */}
  <div style={{ position: "absolute", right: 12 }} />
      </div>

      <div style={{ flex: 1, minHeight: 0, overflow: "hidden", height: "100%" }}>
        <BusinessCalendar data={vm.payload} />
      </div>

    </Card>
  );
};

export default CalendarCard;

