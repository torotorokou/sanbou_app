/**
 * 受入ダッシュボード - Page Component
 * MVC構成の薄いPageレイヤー
 * 
 * レスポンシブデザイン（bp.xl = 1280 を基準）:
 * - mobile/tablet (< 1280px): 全カード縦積み（span=24）
 * - desktop (≥ 1280px): 3列レイアウト（7-12-5列配分）
 * 
 * 実装: useResponsive() で bp.xl (1280px) を判定し、span を動的計算
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
import { useResponsive } from "@/shared";
// (removed curMonth / nextMonth imports since month selection is no longer restricted)

const InboundForecastDashboardPage: React.FC = () => {
  const repository = useMemo(() => new MockInboundForecastRepository(), []);
  const vm = useInboundForecastVM(repository);
  const { flags } = useResponsive();
  // 要件変更: 以前は isXl (>=1280) でデスクトップ挙動だったが、
  // これを ">=768px" に切り替える。isGeMd は 768px 以上を示す。
  const isGeMd = Boolean(flags.isMd || flags.isLg || flags.isXl);

  // ≥768px: 3列レイアウト（7-12-5）、未満: 縦積み（24-24-24）
  const spans = isGeMd
    ? { target: 7, daily: 12, cal: 5 }
    : { target: 24, daily: 24, cal: 24 };

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

        {/* 上段：>=768px は 3列レイアウト、<768px は 2カラム（目標カード左、営業カレンダー右）+ 別行で日次グラフ */}
        <div style={{ minHeight: 0 }}>
          {isGeMd ? (
            <Row gutter={[12, 12]} style={{ height: "100%", alignItems: "stretch" }}>
              {/* Target Card: desktop で7/24列 */}
              <Col span={spans.target} style={{ height: "100%" }}>
                {vm.targetCardProps && <TargetCard {...vm.targetCardProps} />}
              </Col>
              {/* Combined Daily Card: desktop で12/24列 */}
              <Col span={spans.daily} style={{ height: "100%" }}>
                {vm.combinedDailyProps && <CombinedDailyCard {...vm.combinedDailyProps} />}
              </Col>
              {/* Calendar Card: desktop で5/24列 */}
              <Col span={spans.cal} style={{ height: "100%" }}>
                {(() => {
                  const [year, month] = vm.month.split("-").map(Number);
                  return <UkeireCalendarCard year={year} month={month} />;
                })()}
              </Col>
            </Row>
          ) : (
            // <1280px: 1行目に Target (left) / Calendar (right)、2行目に CombinedDaily (full width)
            <>
              <Row gutter={[12, 12]} style={{ height: "100%", alignItems: "stretch" }}>
                {/* Target (left) */}
                <Col span={16} style={{ height: "100%" }}>
                  {vm.targetCardProps && <TargetCard {...vm.targetCardProps} />}
                </Col>
                {/* Calendar (right) */}
                <Col span={8} style={{ height: "100%" }}>
                  {(() => {
                    // vm.month は存在している想定（ロード終わりの分岐内）
                    const safeMonth = vm.month ?? "0000-00";
                    const parts = safeMonth.split("-").map(Number);
                    const year = Number.isNaN(parts[0]) ? undefined : parts[0];
                    const month = Number.isNaN(parts[1]) ? undefined : parts[1];
                    return year && month ? (
                      <UkeireCalendarCard year={year} month={month} />
                    ) : null;
                  })()}
                </Col>
              </Row>

              <Row gutter={[12, 12]} style={{ height: "100%", marginTop: 8 }}>
                <Col span={24} style={{ height: "100%" }}>
                  {vm.combinedDailyProps && <CombinedDailyCard {...vm.combinedDailyProps} />}
                </Col>
              </Row>
            </>
          )}
        </div>

        {/* 下段：予測（常に全幅） */}
        <div style={{ minHeight: 0 }}>
          <Row gutter={[8, 8]} style={{ height: "100%" }}>
            <Col span={24} style={{ height: "100%" }}>
              {vm.forecastCardProps && <ForecastCard {...vm.forecastCardProps} isGeMd={isGeMd} />}
            </Col>
          </Row>
        </div>
      </div>
    </div>
  );
};

export default InboundForecastDashboardPage;
