import React from "react";
import { Row, Col } from "antd";
import type { Dayjs } from "dayjs";
import { PeriodSelector } from "../PeriodSelector";
import type { GridConfig } from "../../config/layout.config";

interface PeriodSectionProps {
  gutter: [number, number];
  periodGrid: GridConfig;
  marginTop: number;

  granularity: "month" | "date";
  periodMode: "single" | "range";
  month: Dayjs;
  range: [Dayjs, Dayjs] | null;
  singleDate: Dayjs;
  dateRange: [Dayjs, Dayjs] | null;
  onGranularityChange: (granularity: "month" | "date") => void;
  onPeriodModeChange: (mode: "single" | "range") => void;
  onMonthChange: (month: Dayjs) => void;
  onRangeChange: (range: [Dayjs, Dayjs] | null) => void;
  onSingleDateChange: (date: Dayjs) => void;
  onDateRangeChange: (range: [Dayjs, Dayjs] | null) => void;
}

/**
 * 期間選択セクション
 *
 * 月次/日次、単一/期間の選択を行う
 */
export const PeriodSection: React.FC<PeriodSectionProps> = ({
  gutter,
  periodGrid,
  marginTop,
  granularity,
  periodMode,
  month,
  range,
  singleDate,
  dateRange,
  onGranularityChange,
  onPeriodModeChange,
  onMonthChange,
  onRangeChange,
  onSingleDateChange,
  onDateRangeChange,
}) => {
  return (
    <Row gutter={gutter} align="middle" style={{ marginTop }}>
      <Col {...periodGrid}>
        <PeriodSelector
          granularity={granularity}
          periodMode={periodMode}
          month={month}
          range={range}
          singleDate={singleDate}
          dateRange={dateRange}
          onGranularityChange={onGranularityChange}
          onPeriodModeChange={onPeriodModeChange}
          onMonthChange={onMonthChange}
          onRangeChange={onRangeChange}
          onSingleDateChange={onSingleDateChange}
          onDateRangeChange={onDateRangeChange}
        />
      </Col>
    </Row>
  );
};
