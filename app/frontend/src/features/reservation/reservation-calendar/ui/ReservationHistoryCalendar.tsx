/**
 * ReservationHistoryCalendar - 予約履歴カレンダー（右側：表示専用）
 * 
 * UI Component (状態レス)
 * 左の入力フォームとは連動しない。履歴表示のみ。
 * 規約: Named Export を使用
 */

import React from 'react';
import { Card, Button, Space, Typography, Spin } from 'antd';
import { LeftOutlined, RightOutlined, TruckOutlined, TeamOutlined } from '@ant-design/icons';
import type { Dayjs } from 'dayjs';
import dayjs from 'dayjs';
import type { ReservationForecastDaily } from '../../shared';

const { Title, Text } = Typography;

const WEEKDAYS = ['月', '火', '水', '木', '金', '土', '日'];

interface ReservationHistoryCalendarProps {
  historyMonth: Dayjs;
  historyData: ReservationForecastDaily[];
  onChangeHistoryMonth: (month: Dayjs) => void;
  isLoadingHistory?: boolean;
}

export const ReservationHistoryCalendar: React.FC<ReservationHistoryCalendarProps> = ({
  historyMonth,
  historyData,
  onChangeHistoryMonth,
  isLoadingHistory = false,
}) => {
  // 月の週データを生成
  const generateWeeks = (month: Dayjs) => {
    const firstDay = month.startOf('month');
    const lastDay = month.endOf('month');
    const startDate = firstDay.startOf('week').add(1, 'day'); // 月曜始まり
    const endDate = lastDay.endOf('week').add(1, 'day');

    const weeks: Dayjs[][] = [];
    let currentWeek: Dayjs[] = [];
    let current = startDate;

    while (current.isBefore(endDate) || current.isSame(endDate, 'day')) {
      currentWeek.push(current);
      if (currentWeek.length === 7) {
        weeks.push(currentWeek);
        currentWeek = [];
      }
      current = current.add(1, 'day');
    }

    return weeks;
  };

  const weeks = generateWeeks(historyMonth);

  const goPrevMonth = () => {
    onChangeHistoryMonth(historyMonth.subtract(1, 'month'));
  };

  const goNextMonth = () => {
    onChangeHistoryMonth(historyMonth.add(1, 'month'));
  };

  // 日付のデータを取得
  const getDataForDate = (date: Dayjs): ReservationForecastDaily | null => {
    const dateStr = date.format('YYYY-MM-DD');
    return historyData.find(d => d.date === dateStr) || null;
  };

  return (
    <Card
      title={
        <Space direction="vertical" size={0} style={{ width: '100%' }}>
          <Title level={5} style={{ margin: 0, fontSize: 16 }}>
            📅 予約履歴カレンダー
          </Title>
        </Space>
      }
      size="small"
      style={{ height: '100%', display: 'flex', flexDirection: 'column' }}
      styles={{ body: { flex: 1, overflow: 'auto', padding: '12px' } }}
    >
      {/* 月移動ヘッダー */}
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', marginBottom: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Button
            type="text"
            icon={<LeftOutlined />}
            onClick={goPrevMonth}
            size="small"
            disabled={isLoadingHistory}
          />
          <Text strong style={{ fontSize: 20, minWidth: 180, textAlign: 'center' }}>
            {historyMonth.format('YYYY年MM月')}
          </Text>
          <Button
            type="text"
            icon={<RightOutlined />}
            onClick={goNextMonth}
            size="small"
            disabled={isLoadingHistory}
          />
        </div>
      </div>

      {/* カレンダー本体 */}
      <Spin spinning={isLoadingHistory}>
        <div style={{ opacity: isLoadingHistory ? 0.5 : 1 }}>
          {/* 曜日ヘッダー */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 2, marginBottom: 4 }}>
            {WEEKDAYS.map((day, idx) => (
              <div
                key={idx}
                style={{
                  textAlign: 'center',
                  fontSize: 13,
                  fontWeight: 'bold',
                  color: idx === 5 ? '#1890ff' : idx === 6 ? '#f5222d' : '#666',
                  padding: '6px 0',
                }}
              >
                {day}
              </div>
            ))}
          </div>

          {/* 日付グリッド */}
          {weeks.map((week, weekIdx) => (
            <div key={weekIdx} style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 2, marginBottom: 2 }}>
              {week.map((date, dayIdx) => {
                const isCurrentMonth = date.month() === historyMonth.month();
                const isToday = date.isSame(dayjs(), 'day');
                const data = getDataForDate(date);

                return (
                  <div
                    key={dayIdx}
                    style={{
                      minHeight: 75,
                      padding: 6,
                      border: '1px solid #f0f0f0',
                      borderRadius: 4,
                      background: isToday ? '#e6f7ff' : isCurrentMonth ? '#fff' : '#fafafa',
                      opacity: isCurrentMonth ? 1 : 0.4,
                      cursor: data ? 'pointer' : 'default',
                    }}
                    title={data ? `合計: ${data.reserve_trucks}, 固定: ${data.reserve_fixed_trucks}` : undefined}
                  >
                    <div style={{ fontSize: 14, fontWeight: isToday ? 'bold' : 'normal', marginBottom: 3 }}>
                      {date.date()}
                    </div>
                    {data && (
                      <div style={{ fontSize: 12, lineHeight: '16px' }}>
                        <div>
                          <TruckOutlined style={{ marginRight: 4, color: '#1890ff' }} />
                          <span style={{ fontSize: 12 }}>{data.reserve_trucks}台</span>
                        </div>
                        <div style={{ color: '#52c41a', marginTop: 3 }}>
                          <TeamOutlined style={{ marginRight: 4 }} />
                          固定: {data.reserve_fixed_trucks}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      </Spin>
    </Card>
  );
};
