/**
 * 受入ダッシュボード - Page Component (useResponsive統合版)
 * MVC構成の薄いPageレイヤー
 * 
 * 🔄 リファクタリング内容：
 * - useResponsive(flags)のflagsベース段階レイアウト
 * - 3パターンレスポンシブ（Mobile/LaptopOrBelow/Desktop）
 * - 値の決定はコンポーネント先頭で一元管理
 * 
 * レスポンシブデザイン:
 * - Mobile (≤767px): 全て1列（縦積み）
 * - LaptopOrBelow (768-1279px): 上段2列（目標/カレンダー）、中段1列（日次）、下段1列（予測）
 * - Desktop (≥1280px): 上段3列（目標/日次/カレンダー）、下段1列（予測）
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

const InboundForecastDashboardPage: React.FC = () => {
  const repository = useMemo(() => new MockInboundForecastRepository(), []);
  const vm = useInboundForecastVM(repository);
  
  // responsive: flagsベースレイアウト
  const { flags } = useResponsive();

  // responsive: レイアウトモード判定
  type LayoutMode = "mobile" | "laptopOrBelow" | "desktop";
  const layoutMode: LayoutMode = flags.isMobile 
    ? "mobile" 
    : (flags.isTablet || flags.isLaptop) 
      ? "laptopOrBelow" 
      : "desktop";

  // responsive: ガッター・余白（段階的）
  const gutter = flags.isMobile ? 8 : flags.isTablet ? 12 : flags.isLaptop ? 16 : 20;
  const padding = flags.isMobile ? 8 : flags.isTablet ? 12 : flags.isLaptop ? 16 : 16;

  // responsive: カラムspan定義
  const spans = {
    mobile: { target: 24, daily: 24, cal: 24 },           // 全て1列
    laptopOrBelow: { target: 12, daily: 24, cal: 12 },    // 上段2列、中段1列
    desktop: { target: 7, daily: 12, cal: 5 }             // 上段3列
  }[layoutMode];

  // responsive: flagsベースレイアウト修正 - fix: chart visibility
  // レイアウトモード変更時にresizeイベントを発火し、Rechartsの再描画を促す
  React.useEffect(() => {
    const id = setTimeout(() => {
      window.dispatchEvent(new Event("resize"));
    }, 0);
    return () => clearTimeout(id);
  }, [layoutMode]);

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
            padding,
            boxSizing: "border-box",
            flex: 1,
            minHeight: 0,
            overflowY: "auto",
            scrollbarGutter: "stable",
          }}
        >
          <Row gutter={[gutter, gutter]} style={{ height: "100%", alignItems: "stretch" }}>
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
          padding,
          boxSizing: "border-box",
          flex: 1,
          minHeight: 0,
          overflowY: "auto",
          scrollbarGutter: "stable",
        }}
      >
        {/* ヘッダー */}
        <div style={{ marginBottom: gutter }}>
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

        {/* 上段：responsive: flagsベースレイアウト分岐 */}
        <div style={{ marginBottom: gutter }}>
          <Row gutter={[gutter, gutter]}>
            {layoutMode === "mobile" ? (
              // responsive: flagsベースレイアウト修正 - Mobile: 全て1列（縦積み）
              // 順序: 目標 → カレンダー → 日次グラフ
              <>
                <Col span={spans.target}>
                  <div style={{ height: 280 }}>
                    {vm.targetCardProps && <TargetCard {...vm.targetCardProps} />}
                  </div>
                </Col>
                <Col span={spans.cal}>
                  <div style={{ height: 320 }}>
                    {(() => {
                      if (!vm.month) return null;
                      const [year, month] = vm.month.split("-").map(Number);
                      if (!year || !month || Number.isNaN(year) || Number.isNaN(month)) return null;
                      return <UkeireCalendarCard year={year} month={month} />;
                    })()}
                  </div>
                </Col>
                <Col span={spans.daily}>
                  <div style={{ height: 380 }}>
                    {vm.combinedDailyProps && <CombinedDailyCard {...vm.combinedDailyProps} />}
                  </div>
                </Col>
              </>
            ) : layoutMode === "laptopOrBelow" ? (
              // responsive: flagsベースレイアウト修正 - LaptopOrBelow: 上段2列（目標/カレンダー）、中段1列（日次）
              <>
                <Col span={spans.target}>
                  <div style={{ height: 320 }}>
                    {vm.targetCardProps && <TargetCard {...vm.targetCardProps} />}
                  </div>
                </Col>
                <Col span={spans.cal}>
                  <div style={{ height: 320 }}>
                    {(() => {
                      if (!vm.month) return null;
                      const [year, month] = vm.month.split("-").map(Number);
                      if (!year || !month || Number.isNaN(year) || Number.isNaN(month)) return null;
                      return <UkeireCalendarCard year={year} month={month} />;
                    })()}
                  </div>
                </Col>
                <Col span={spans.daily}>
                  <div style={{ height: 400 }}>
                    {vm.combinedDailyProps && <CombinedDailyCard {...vm.combinedDailyProps} />}
                  </div>
                </Col>
              </>
            ) : (
              // responsive: flagsベースレイアウト修正 - Desktop: 上段3列（目標/日次/カレンダー）
              <>
                <Col span={spans.target}>
                  <div style={{ height: 360 }}>
                    {vm.targetCardProps && <TargetCard {...vm.targetCardProps} />}
                  </div>
                </Col>
                <Col span={spans.daily}>
                  <div style={{ height: 360 }}>
                    {vm.combinedDailyProps && <CombinedDailyCard {...vm.combinedDailyProps} />}
                  </div>
                </Col>
                <Col span={spans.cal}>
                  <div style={{ height: 360 }}>
                    {(() => {
                      if (!vm.month) return null;
                      const [year, month] = vm.month.split("-").map(Number);
                      if (!year || !month || Number.isNaN(year) || Number.isNaN(month)) return null;
                      return <UkeireCalendarCard year={year} month={month} />;
                    })()}
                  </div>
                </Col>
              </>
            )}
          </Row>
        </div>

        {/* 下段：予測（常に全幅） */}
        <div>
          <Row gutter={[gutter, gutter]}>
            <Col span={24}>
              <div style={{ height: layoutMode === "mobile" ? 640 : 420 }}>
                {vm.forecastCardProps && <ForecastCard {...vm.forecastCardProps} isGeMd={layoutMode !== "mobile"} />}
              </div>
            </Col>
          </Row>
        </div>
      </div>
    </div>
  );
};

export default InboundForecastDashboardPage;
