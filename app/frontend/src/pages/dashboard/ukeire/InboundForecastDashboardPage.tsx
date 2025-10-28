/**
 * 受入ダッシュボード - Page Component
 * 
 * 責務：ページレイアウトの骨組みのみ
 * - ViewModel（useInboundForecastVM）からデータを取得
 * - レスポンシブレイアウト設定（useResponsiveLayout）
 * - UI部品（MonthNavigator, Card系）の配置
 * 
 * ロジック・状態管理・API呼び出しは全てFeatures層に分離済み
 */

import React, { useMemo } from "react";
import { Row, Col, Skeleton } from "antd";
import dayjs from "dayjs";
import { 
  useInboundForecastVM,
  MockInboundForecastRepository,
  TargetCard,
  CombinedDailyCard,
  UkeireCalendarCard,
  ForecastCard,
  MonthNavigator,
  useResponsiveLayout
} from "@/features/dashboard/ukeire";
import styles from "./InboundForecastDashboardPage.module.css";

const InboundForecastDashboardPage: React.FC = () => {
  const repository = useMemo(() => new MockInboundForecastRepository(), []);
  const vm = useInboundForecastVM(repository);
  const layout = useResponsiveLayout();

  // 月ナビゲーション用のハンドラ
  const handlePrevMonth = () => {
    const current = vm.month ? dayjs(vm.month, "YYYY-MM") : dayjs();
    const prev = current.add(-1, "month").format("YYYY-MM");
    vm.setMonth(prev);
  };

  const handleNextMonth = () => {
    const current = vm.month ? dayjs(vm.month, "YYYY-MM") : dayjs();
    const next = current.add(1, "month").format("YYYY-MM");
    vm.setMonth(next);
  };

  if (vm.loading || !vm.payload) {
    return (
      <div className={styles.pageContainer} style={{ padding: layout.padding }}>
        <div className={styles.contentWrapper}>
          <Row gutter={[layout.gutter, layout.gutter]}>
            <Col span={24}><Skeleton active paragraph={{ rows: 6 }} /></Col>
            <Col span={24}><Skeleton active paragraph={{ rows: 6 }} /></Col>
            <Col span={24}><Skeleton active paragraph={{ rows: 6 }} /></Col>
          </Row>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.pageContainer}>
      <div className={styles.contentWrapper} style={{ padding: layout.padding }}>
        {/* ヘッダー：月ナビゲーション */}
        <div style={{ marginBottom: layout.gutter }}>
          <MonthNavigator
            title="搬入量ダッシュボード"
            month={vm.month}
            monthJP={layout.mode !== "mobile" ? vm.monthJP : undefined}
            todayBadge={vm.headerProps?.todayBadge}
            isMobile={layout.mode === "mobile"}
            onMonthChange={vm.setMonth}
            onPrevMonth={handlePrevMonth}
            onNextMonth={handleNextMonth}
          />
        </div>

        {/* 上段：レスポンシブレイアウト分岐 */}
        <div 
          style={{ 
            marginBottom: layout.gutter, 
            flex: layout.mode === "desktop" ? "1" : "0 0 auto", 
            minHeight: 0 
          }}
        >
          <Row gutter={[layout.gutter, layout.gutter]} style={{ height: layout.mode === "desktop" ? "100%" : "auto" }}>
            {layout.mode === "mobile" ? (
              // Mobile: 目標カードのみ（予測と日次は下段へ）
              <Col span={layout.spans.target}>
                <div style={{ height: layout.heights.target.mobile }}>
                  {vm.targetCardProps && <TargetCard {...vm.targetCardProps} isMobile={true} />}
                </div>
              </Col>
            ) : layout.mode === "laptopOrBelow" ? (
              // LaptopOrBelow: 上段2列（目標/カレンダー）、中段1列（日次）
              <>
                <Col span={layout.spans.target}>
                  <div style={{ height: layout.heights.target.laptopOrBelow }}>
                    {vm.targetCardProps && <TargetCard {...vm.targetCardProps} />}
                  </div>
                </Col>
                <Col span={layout.spans.cal}>
                  <div style={{ height: layout.heights.calendar.laptopOrBelow }}>
                    {(() => {
                      if (!vm.month) return null;
                      const [year, month] = vm.month.split("-").map(Number);
                      if (!year || !month || Number.isNaN(year) || Number.isNaN(month)) return null;
                      return <UkeireCalendarCard year={year} month={month} />;
                    })()}
                  </div>
                </Col>
                <Col span={layout.spans.daily}>
                  <div style={{ height: layout.heights.daily.laptopOrBelow }}>
                    {vm.combinedDailyProps && <CombinedDailyCard {...vm.combinedDailyProps} />}
                  </div>
                </Col>
              </>
            ) : (
              // Desktop: 上段3列（目標/日次/カレンダー）
              <>
                <Col span={layout.spans.target} style={{ height: "100%" }}>
                  <div style={{ height: layout.heights.target.desktop }}>
                    {vm.targetCardProps && <TargetCard {...vm.targetCardProps} />}
                  </div>
                </Col>
                <Col span={layout.spans.daily} style={{ height: "100%" }}>
                  <div style={{ height: layout.heights.daily.desktop }}>
                    {vm.combinedDailyProps && <CombinedDailyCard {...vm.combinedDailyProps} />}
                  </div>
                </Col>
                <Col span={layout.spans.cal} style={{ height: "100%" }}>
                  <div style={{ height: layout.heights.calendar.desktop }}>
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

        {/* 下段：予測カード（全幅） */}
        <div style={{ flex: layout.mode === "desktop" ? "1" : "0 0 auto", minHeight: 0 }}>
          <Row gutter={[layout.gutter, layout.gutter]} style={{ height: layout.mode === "desktop" ? "100%" : "auto" }}>
            {layout.mode === "mobile" ? (
              // Mobile: 予測 → 日次の順
              <>
                <Col span={24}>
                  <div style={{ height: layout.heights.forecast.mobile }}>
                    {vm.forecastCardProps && <ForecastCard {...vm.forecastCardProps} isGeMd={false} />}
                  </div>
                </Col>
                <Col span={24}>
                  <div style={{ height: layout.heights.daily.mobile }}>
                    {vm.combinedDailyProps && <CombinedDailyCard {...vm.combinedDailyProps} />}
                  </div>
                </Col>
              </>
            ) : (
              // Desktop/LaptopOrBelow: 予測のみ
              <Col span={24} style={{ height: layout.mode === "desktop" ? "100%" : "auto" }}>
                <div style={{ height: layout.mode === "desktop" ? layout.heights.forecast.desktop : layout.heights.forecast.laptopOrBelow }}>
                  {vm.forecastCardProps && <ForecastCard {...vm.forecastCardProps} isGeMd={true} />}
                </div>
              </Col>
            )}
          </Row>
        </div>
      </div>
    </div>
  );
};

export default InboundForecastDashboardPage;
