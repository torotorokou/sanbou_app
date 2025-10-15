/**
 * 受入ダッシュボード - Page Component
 * MVC構成の薄いPageレイヤー
 */

import React, { useMemo } from "react";
import { Row, Col, Typography, DatePicker, Space, Badge, Skeleton } from "antd";
import dayjs from "dayjs";
import { useUkeireForecastVM } from "@/features/dashboard/ukeire/application/useUkeireForecastVM";
import { MockInboundForecastRepository } from "@/features/dashboard/ukeire/application/adapters/mock.repository";
import { TargetCard } from "@/features/dashboard/ukeire/ui/cards/TargetCard";
import { CombinedDailyCard } from "@/features/dashboard/ukeire/ui/cards/CombinedDailyCard";
import { CalendarCard } from "@/features/dashboard/ukeire/ui/cards/CalendarCard";
import { ForecastCard } from "@/features/dashboard/ukeire/ui/cards/ForecastCard";
import { curMonth, nextMonth } from "@/features/dashboard/ukeire/domain/valueObjects";

const InboundForecastDashboardPage: React.FC = () => {
  const repository = useMemo(() => new MockInboundForecastRepository(), []);
  const vm = useUkeireForecastVM(repository);

  if (vm.loading || !vm.payload) {
    return (
      <div
        style={{
          minHeight: "100dvh",
          overflow: "hidden",
          padding: 0,
          boxSizing: "border-box",
          display: "flex",
          flexDirection: "column",
          scrollbarGutter: "stable",
        }}
      >
        <div
          style={{
            padding: 12,
            boxSizing: "border-box",
            flex: 1,
            minHeight: 0,
            overflowY: "auto",
            scrollbarGutter: "stable",
          }}
        >
          <Row gutter={[12, 12]} style={{ height: "100%", alignItems: "stretch" }}>
            <Col span={24}>
              <Skeleton active paragraph={{ rows: 6 }} />
            </Col>
            <Col span={24}>
              <Skeleton active paragraph={{ rows: 6 }} />
            </Col>
            <Col span={24}>
              <Skeleton active paragraph={{ rows: 6 }} />
            </Col>
          </Row>
        </div>
      </div>
    );
  }

  return (
    <div
      style={{
        minHeight: "100dvh",
        overflow: "hidden",
        display: "flex",
        flexDirection: "column",
        padding: 0,
        boxSizing: "border-box",
        scrollbarGutter: "stable",
      }}
    >
      <div
        style={{
          padding: 12,
          boxSizing: "border-box",
          flex: 1,
          minHeight: 0,
          display: "grid",
          gridTemplateRows: "auto 1fr 1.2fr",
          rowGap: 8,
          overflowY: "auto",
          scrollbarGutter: "stable",
        }}
      >
        {/* ヘッダー */}
        <div>
          <Row justify="space-between" align="middle">
            <Col>
              <Typography.Title level={4} style={{ margin: 0 }}>
                搬入量ダッシュボード — {vm.monthJP}
              </Typography.Title>
            </Col>
            <Col>
              <Space size={8} wrap>
                <DatePicker
                  picker="month"
                  value={dayjs(vm.month, "YYYY-MM")}
                  onChange={(_, s) => typeof s === "string" && vm.setMonth(s)}
                  disabledDate={(d) => {
                    if (!d) return false;
                    const ym = d.format("YYYY-MM");
                    const min = curMonth();
                    const max = nextMonth(curMonth());
                    return ym < min || ym > max;
                  }}
                  style={{ width: 140 }}
                  size="small"
                />
                <Badge count={vm.headerProps?.todayBadge ?? ""} style={{ backgroundColor: "#1677ff" }} />
              </Space>
            </Col>
          </Row>
        </div>

        {/* 上段：3カード */}
        <div style={{ minHeight: 0 }}>
          <Row gutter={[12, 12]} style={{ height: "100%", alignItems: "stretch" }}>
            <Col xs={24} lg={7} style={{ height: "100%" }}>
              {vm.targetCardProps && <TargetCard {...vm.targetCardProps} />}
            </Col>
            <Col xs={24} lg={12} style={{ height: "100%" }}>
              {vm.combinedDailyProps && <CombinedDailyCard {...vm.combinedDailyProps} />}
            </Col>
            <Col xs={24} lg={5} style={{ height: "100%" }}>
              <CalendarCard month={vm.month} />
            </Col>
          </Row>
        </div>

        {/* 下段：予測 */}
        <div style={{ minHeight: 0 }}>
          <Row gutter={[8, 8]} style={{ height: "100%" }}>
            <Col xs={24} style={{ height: "100%" }}>
              {vm.forecastCardProps && <ForecastCard {...vm.forecastCardProps} />}
            </Col>
          </Row>
        </div>
      </div>
    </div>
  );
};

export default InboundForecastDashboardPage;
