/**
 * ReservationCalendar - 予約カレンダー表示
 * 
 * UI Component
 */

import React from 'react';
import { Calendar, Badge, Typography } from 'antd';
import type { Dayjs } from 'dayjs';
import dayjs from 'dayjs';
import type { ReservationForecastDaily } from '../ports/ReservationDailyRepository';

const { Text } = Typography;

interface ReservationCalendarProps {
  currentMonth: Dayjs;
  forecastData: ReservationForecastDaily[];
  selectedDate: string | null;
  onChangeMonth: (month: Dayjs) => void;
  onSelectDate: (date: string) => void;
  isLoading?: boolean;
}

export const ReservationCalendar: React.FC<ReservationCalendarProps> = ({
  currentMonth,
  forecastData,
  selectedDate,
  onChangeMonth,
  onSelectDate,
  isLoading = false,
}) => {
  const dateCellRender = (date: Dayjs) => {
    const dateStr = date.format('YYYY-MM-DD');
    const data = forecastData.find(d => d.date === dateStr);

    if (!data) return null;

    const isManual = data.source === 'manual';

    return (
      <div style={{ fontSize: '11px', lineHeight: '14px' }}>
        <Badge 
          status={isManual ? 'success' : 'processing'} 
          text={`合計: ${data.reserve_trucks}`}
        />
        <br />
        <Text type="secondary" style={{ fontSize: '10px' }}>
          固定: {data.reserve_fixed_trucks}
        </Text>
      </div>
    );
  };

  const handleSelect = (date: Dayjs) => {
    onSelectDate(date.format('YYYY-MM-DD'));
  };

  const handlePanelChange = (date: Dayjs) => {
    onChangeMonth(date);
  };

  return (
    <div style={{ opacity: isLoading ? 0.5 : 1 }}>
      <Calendar
        value={currentMonth}
        dateCellRender={dateCellRender}
        onSelect={handleSelect}
        onPanelChange={handlePanelChange}
        fullscreen={false}
      />
    </div>
  );
};
