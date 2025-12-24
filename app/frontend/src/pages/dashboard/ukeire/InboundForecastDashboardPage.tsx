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

import React, { useMemo, useState } from "react";
import { Row, Col, Skeleton, Alert } from "antd";
import dayjs from "dayjs";
import isoWeek from "dayjs/plugin/isoWeek";
import { 
  useInboundForecastVM,
  MockInboundForecastRepository,
  TargetCard,
  CombinedDailyCard,
  UkeireCalendarCard,
  ForecastCard,
  MonthNavigator,
  useResponsiveLayout,
  useTargetMetrics,
  useInboundMonthlyVM,
  HttpInboundDailyRepository,
  CalendarRepositoryForUkeire,
  useTargetsVM,
  type AchievementMode,
} from "@/features/dashboard/ukeire";
import styles from "./InboundForecastDashboardPage.module.css";

// dayjs の isoWeek プラグインを有効化
dayjs.extend(isoWeek);

const InboundForecastDashboardPage: React.FC = () => {
  // 初期月を先に確定
  const initialMonth = useMemo(() => dayjs().format("YYYY-MM"), []);
  
  const repository = useMemo(() => new MockInboundForecastRepository(), []);
  const vm = useInboundForecastVM(repository, initialMonth);
  const layout = useResponsiveLayout();

  // 選択中の月が当月かどうかを判定
  const isCurrentMonth = useMemo(() => {
    if (!vm.month) return true;
    const selectedMonth = dayjs(vm.month, "YYYY-MM").format("YYYY-MM");
    const currentMonth = dayjs().format("YYYY-MM");
    return selectedMonth === currentMonth;
  }, [vm.month]);

  // 達成率モードの状態管理(デフォルト: 昨日までの累計目標に対する達成率)
  // ※当月以外では常に"toEnd"モードに固定
  const [achievementMode, setAchievementMode] = useState<AchievementMode>("toDate");
  const effectiveMode: AchievementMode = isCurrentMonth ? achievementMode : "toEnd";

  // 選択中の月から対象日付を計算（月の初日を使用してAPIに渡す）
  // ※Backend側で該当月の適切な日付（当月=today, 過去=月末, 未来=月初営業日）を自動解決
  const targetDate = useMemo(() => {
    return dayjs(vm.month, "YYYY-MM").startOf("month").format("YYYY-MM-DD");
  }, [vm.month]);
  
  // DBから目標値と実績値を取得（選択月に応じて動的に変更、mode=monthlyで過去/未来は日週マスク）
  const { data: targetMetrics, error: targetError } = useTargetMetrics(targetDate, "monthly");

  // 日次搬入量データ用のリポジトリとVM（営業カレンダーリポジトリを追加）
  const dailyRepository = useMemo(() => new HttpInboundDailyRepository(), []);
  const calendarRepository = useMemo(() => new CalendarRepositoryForUkeire(), []);
  const dailyVM = useInboundMonthlyVM({
    repository: dailyRepository,
    calendarRepository,
    month: vm.month,
  });

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

  // useTargetsVM で達成率モードに応じた目標カードデータを生成
  // ※当月以外では週次・日次を非表示にするため、該当フィールドにnullを渡す
  const targetCardVM = useTargetsVM({
    mode: effectiveMode,
    monthTargetToDate: targetMetrics?.month_target_to_date_ton ?? null,
    weekTargetToDate: targetMetrics?.week_target_to_date_ton ?? null,
    dayTarget: targetMetrics?.day_target_ton ?? null,
    monthTargetTotal: targetMetrics?.month_target_total_ton ?? null,
    weekTargetTotal: targetMetrics?.week_target_total_ton ?? null,
    todayActual: targetMetrics?.day_actual_ton_prev ?? null,
    weekActual: targetMetrics?.week_actual_to_date_ton ?? null,
    monthActual: targetMetrics?.month_actual_to_date_ton ?? null,
    hideWeekAndDay: !isCurrentMonth, // 当月以外は週次・日次を非表示
  });

  // DBから取得したISO週番号を使用（NULLの場合は現在の週番号）
  const isoWeek = useMemo(() => {
    return targetMetrics?.iso_week ?? dayjs().isoWeek();
  }, [targetMetrics]);

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
            minHeight: 0,
            display: "flex",
            flexDirection: "column"
          }}
        >
          <Row gutter={[layout.gutter, layout.gutter]} style={{ height: layout.mode === "desktop" ? "100%" : "auto", flex: layout.mode === "desktop" ? 1 : "none" }}>
            {layout.mode === "mobile" ? (
              // Mobile: 目標カードのみ（予測と日次は下段へ）
              <Col span={layout.spans.target}>
                <div>
                  {targetError ? (
                    <Alert
                      message="目標データ取得エラー"
                      description={targetError.message}
                      type="error"
                      showIcon
                    />
                  ) : !targetMetrics ? (
                    <Alert
                      message="データ読み込み中"
                      description="目標データを読み込んでいます..."
                      type="info"
                      showIcon
                    />
                  ) : (
                    <TargetCard 
                      rows={targetCardVM.rows} 
                      isoWeek={isoWeek} 
                      isMobile={true}
                      achievementMode={effectiveMode}
                      onModeChange={isCurrentMonth ? setAchievementMode : undefined}
                    />
                  )}
                </div>
              </Col>
            ) : layout.mode === "tablet" ? (
              // Tablet: 上段2列（目標/カレンダー）、中段1列（日次）
              <>
                <Col span={layout.spans.target}>
                  <div style={{ height: layout.heights.target.tablet }}>
                    {targetError ? (
                      <Alert
                        message="目標データ取得エラー"
                        description={targetError.message}
                        type="error"
                        showIcon
                      />
                    ) : !targetMetrics ? (
                      <Alert
                        message="データ読み込み中"
                        description="目標データを読み込んでいます..."
                        type="info"
                        showIcon
                      />
                    ) : (
                      <TargetCard 
                        rows={targetCardVM.rows} 
                        isoWeek={isoWeek}
                        achievementMode={effectiveMode}
                        onModeChange={isCurrentMonth ? setAchievementMode : undefined}
                      />
                    )}
                  </div>
                </Col>
                <Col span={layout.spans.cal}>
                  <div style={{ height: layout.heights.calendar.tablet }}>
                    {(() => {
                      if (!vm.month) return null;
                      const [year, month] = vm.month.split("-").map(Number);
                      if (!year || !month || Number.isNaN(year) || Number.isNaN(month)) return null;
                      return <UkeireCalendarCard year={year} month={month} />;
                    })()}
                  </div>
                </Col>
                <Col span={layout.spans.daily}>
                  <div style={{ height: layout.heights.daily.tablet }}>
                    {dailyVM.loading ? (
                      <Skeleton active paragraph={{ rows: 4 }} />
                    ) : dailyVM.error ? (
                      <Alert
                        message="日次データ取得エラー"
                        description={dailyVM.error.message}
                        type="error"
                        showIcon
                        style={{ height: "100%" }}
                      />
                    ) : dailyVM.dailyProps && dailyVM.cumulativeProps ? (
                      <CombinedDailyCard 
                        dailyProps={dailyVM.dailyProps} 
                        cumulativeProps={dailyVM.cumulativeProps} 
                      />
                    ) : null}
                  </div>
                </Col>
              </>
            ) : (
              // Desktop: 上段3列（目標/日次/カレンダー）
              <>
                <Col span={layout.spans.target} style={{ height: "100%" }}>
                  <div style={{ height: layout.heights.target.desktop }}>
                    {targetError ? (
                      <Alert
                        message="目標データ取得エラー"
                        description={targetError.message}
                        type="error"
                        showIcon
                      />
                    ) : !targetMetrics ? (
                      <Alert
                        message="データ読み込み中"
                        description="目標データを読み込んでいます..."
                        type="info"
                        showIcon
                      />
                    ) : (
                      <TargetCard 
                        rows={targetCardVM.rows} 
                        isoWeek={isoWeek}
                        achievementMode={effectiveMode}
                        onModeChange={isCurrentMonth ? setAchievementMode : undefined}
                      />
                    )}
                  </div>
                </Col>
                <Col span={layout.spans.daily} style={{ height: "100%" }}>
                  <div style={{ height: layout.heights.daily.desktop }}>
                    {dailyVM.loading ? (
                      <Skeleton active paragraph={{ rows: 4 }} />
                    ) : dailyVM.error ? (
                      <Alert
                        message="日次データ取得エラー"
                        description={dailyVM.error.message}
                        type="error"
                        showIcon
                        style={{ height: "100%" }}
                      />
                    ) : dailyVM.dailyProps && dailyVM.cumulativeProps ? (
                      <CombinedDailyCard 
                        dailyProps={dailyVM.dailyProps} 
                        cumulativeProps={dailyVM.cumulativeProps} 
                      />
                    ) : null}
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
        <div style={{ flex: layout.mode === "desktop" ? "1" : "0 0 auto", minHeight: 0, display: "flex", flexDirection: "column" }}>
          <Row gutter={[layout.gutter, layout.gutter]} style={{ height: layout.mode === "desktop" ? "100%" : "auto", flex: layout.mode === "desktop" ? 1 : "none" }}>
            {layout.mode === "mobile" ? (
              // Mobile: 日次 → 予測の順
              <>
                <Col span={24}>
                  <div style={{ height: layout.heights.daily.mobile }}>
                    {dailyVM.loading ? (
                      <Skeleton active paragraph={{ rows: 4 }} />
                    ) : dailyVM.error ? (
                      <Alert
                        message="日次データ取得エラー"
                        description={dailyVM.error.message}
                        type="error"
                        showIcon
                        style={{ height: "100%" }}
                      />
                    ) : dailyVM.dailyProps && dailyVM.cumulativeProps ? (
                      <CombinedDailyCard 
                        dailyProps={dailyVM.dailyProps} 
                        cumulativeProps={dailyVM.cumulativeProps} 
                      />
                    ) : null}
                  </div>
                </Col>
                <Col span={24}>
                  <div style={{ height: layout.heights.forecast.mobile }}>
                    {vm.forecastCardProps && <ForecastCard {...vm.forecastCardProps} isGeMd={false} showWipNotice={true} />}
                  </div>
                </Col>
              </>
            ) : (
              // Desktop/Tablet: 予測のみ
              <Col span={24} style={{ height: layout.mode === "desktop" ? "100%" : "auto" }}>
                <div style={{ height: layout.mode === "desktop" ? layout.heights.forecast.desktop : layout.heights.forecast.tablet }}>
                  {vm.forecastCardProps && <ForecastCard {...vm.forecastCardProps} isGeMd={true} showWipNotice={true} />}
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
