/**
 * 受入量ダッシュボードページ
 * レイアウト/配置のみ - ビジネスロジックは overview VM に集約
 */

import React, { useMemo } from "react";
import { Row, Col, Typography, DatePicker, Space, Badge, Skeleton } from "antd";
import dayjs, { type Dayjs } from "dayjs";
import { useUkeireVolumeCombinedVM } from "@/features/ukeireVolume/overview/hooks/useUkeireVolumeCombinedVM";
import { MockUkeireForecastRepository } from "@/features/ukeireVolume/forecast/repository/__mocks__/MockUkeireForecastRepository";
// eslint-disable-next-line @typescript-eslint/no-unused-vars
import type { UkeireActualsRepository } from "@/features/ukeireVolume/actuals/repository/UkeireActualsRepository";
// eslint-disable-next-line @typescript-eslint/no-unused-vars
import type { UkeireHistoryRepository } from "@/features/ukeireVolume/history/repository/UkeireHistoryRepository";
import { TargetCard } from "@/features/kpiTarget/ui/TargetCard";
import CalendarCardUkeire from "@/features/ukeireVolume/actuals/ui/CalendarCard.Ukeire";
import { CombinedDailyCard } from "@/features/ukeireVolume/history/ui/CombinedDailyCard";
import { ForecastCard } from "@/features/ukeireVolume/forecast/ui/ForecastCard";

// TODO: Repository injection should be done at app root level
// For now, create mock repositories here
class MockActualsRepository implements UkeireActualsRepository {
  async fetchDailyActuals() {
    await new Promise((r) => setTimeout(r, 100));
    return { days: [], calendar: [] };
  }
}

class MockHistoryRepository implements UkeireHistoryRepository {
  async fetchHistoricalData() {
    await new Promise((r) => setTimeout(r, 100));
    return { prev_month_daily: {}, prev_year_daily: {} };
  }
}

const UkeirePage: React.FC = () => {
  const actualsRepository = useMemo(() => new MockActualsRepository(), []);
  const historyRepository = useMemo(() => new MockHistoryRepository(), []);
  const forecastRepository = useMemo(() => new MockUkeireForecastRepository(), []);

  const vm = useUkeireVolumeCombinedVM({
    actualsRepository,
    historyRepository,
    forecastRepository,
  });

  if (vm.loading || !vm.targetCardProps) {
    return (
      <div style={{ minHeight: "100dvh", padding: 12 }}>
        <Skeleton active paragraph={{ rows: 6 }} />
      </div>
    );
  }

  return (
    <div
      style={{
        height: "100vh",
        overflow: "hidden",
        display: "flex",
        flexDirection: "column",
        padding: 0,
        boxSizing: "border-box",
      }}
    >
      <div
        style={{
          padding: 12,
          boxSizing: "border-box",
          flex: 1,
          minHeight: 0,
          overflowY: "auto",
        }}
      >
        {/* ヘッダー */}
        <Row align="middle" style={{ marginBottom: 12 }}>
          <Col flex="1" />
          <Col flex="none" style={{ textAlign: "center" }}>
            <Typography.Title level={4} style={{ margin: 0 }}>
              搬入量ダッシュボード — {vm.monthJP}
            </Typography.Title>
          </Col>
          <Col flex="1" style={{ display: "flex", justifyContent: "flex-end" }}>
            <Space size={8} wrap>
              <DatePicker
                picker="month"
                value={vm.month ? dayjs(vm.month, "YYYY-MM") : null}
                onChange={(d: Dayjs | null, s: string | string[]) => {
                  if (d && d.isValid && d.isValid() && typeof s === "string" && s) {
                    vm.setMonth(s);
                  }
                }}
                size="small"
              />
              <Badge count={vm.headerProps?.todayBadge ?? ""} style={{ backgroundColor: "#1677ff" }} />
            </Space>
          </Col>
        </Row>

        {/* 上段：3カード */}
        <Row gutter={[12, 12]} style={{ marginBottom: 12 }}>
          <Col xs={24} lg={7} style={{ minHeight: 400, maxHeight: 500 }}>
            {vm.targetCardProps && <TargetCard {...vm.targetCardProps} />}
          </Col>
          <Col xs={24} lg={12} style={{ minHeight: 400, maxHeight: 500 }}>
            {vm.combinedDailyProps && <CombinedDailyCard {...vm.combinedDailyProps} />}
          </Col>
          <Col xs={24} lg={5} style={{ minHeight: 400, maxHeight: 500 }}>
            {(() => {
              const [year, month] = vm.month.split("-").map(Number);
              return <CalendarCardUkeire year={year} month={month} />;
            })()}
          </Col>
        </Row>

        {/* 下段：予測 */}
        <Row gutter={[12, 12]}>
          <Col xs={24} style={{ minHeight: 400, maxHeight: 600 }}>
            {vm.forecastCardProps && <ForecastCard {...vm.forecastCardProps} />}
          </Col>
        </Row>
      </div>
    </div>
  );
};

export default UkeirePage;
