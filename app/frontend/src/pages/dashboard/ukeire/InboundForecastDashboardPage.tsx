/**
 * 受入ダッシュボード - Page Component
 * MVC構成の薄いPageレイヤー
 * 
 * レスポンシブデザイン:
 * - xs/sm/md (0-1199px): 全カード縦積み（span=24）
 * - xl+ (1200px以上): 3列レイアウト（7-12-5列配分）
 * 
 * 注意: Ant Designのブレークポイントを使用
 * - lg (Ant): 992px ≠ bp.lg (1024px)  
 * - xl (Ant): 1200px = bp.xl (1280px)に近い
 * ※ プロジェクトの bp.xl (1280px) に近い xl を採用
 */

import React, { useMemo } from "react";
import { Row, Col, Typography, DatePicker, Space, Badge, Skeleton } from "antd";
import dayjs from "dayjs";
import type { Dayjs } from "dayjs";
import { 
  useInboundForecastVM,
  MockInboundForecastRepository,
  TargetCard,
  CombinedDailyCard,
  UkeireCalendarCard,
  ForecastCard
} from "@/features/dashboard/ukeire";
// (removed curMonth / nextMonth imports since month selection is no longer restricted)

const InboundForecastDashboardPage: React.FC = () => {
  const repository = useMemo(() => new MockInboundForecastRepository(), []);
  const vm = useInboundForecastVM(repository);

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
        className="inbound-forecast-grid"
        style={{
          padding: 12,
          boxSizing: "border-box",
          flex: 1,
          minHeight: 0,
          overflowY: "auto",
          scrollbarGutter: "stable",
        }}
      >
        {/* ヘッダー */}
        <div>
          {/* 3カラム構成: 左（空）/ 中央（タイトル）/ 右（アクション） */}
          <Row align="middle">
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
                  // vm.month が falsy の時は null を渡して DatePicker をクリア表示にする
                  value={vm.month ? dayjs(vm.month, "YYYY-MM") : null}
                  onChange={(d: Dayjs | null, s: string | string[]) => {
                    // d: Dayjs | null, s: string | string[]
                    // 空や無効な日付は無視する（クリア操作で来る空文字や配列を防ぐ）
                    if (d && d.isValid && d.isValid() && typeof s === "string" && s) {
                      vm.setMonth(s);
                    }
                  }}
                  className="dashboard-month-picker"
                  size="small"
                />
                <Badge count={vm.headerProps?.todayBadge ?? ""} style={{ backgroundColor: "#1677ff" }} />
              </Space>
            </Col>
          </Row>
        </div>

        {/* 上段：3カード（xl以上[1200px+]で3列、未満で縦積み） */}
        <div style={{ minHeight: 0 }}>
          <Row gutter={[12, 12]} style={{ height: "100%", alignItems: "stretch" }}>
            {/* Target Card: xl以上で7/24列、未満で全幅 */}
            <Col xs={24} xl={7} style={{ height: "100%" }}>
              {vm.targetCardProps && <TargetCard {...vm.targetCardProps} />}
            </Col>
            {/* Combined Daily Card: xl以上で12/24列、未満で全幅 */}
            <Col xs={24} xl={12} style={{ height: "100%" }}>
              {vm.combinedDailyProps && <CombinedDailyCard {...vm.combinedDailyProps} />}
            </Col>
            {/* Calendar Card: xl以上で5/24列、未満で全幅 */}
            <Col xs={24} xl={5} style={{ height: "100%" }}>
              {(() => {
                const [year, month] = vm.month.split('-').map(Number);
                return <UkeireCalendarCard year={year} month={month} />;
              })()}
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
