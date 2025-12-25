/**
 * DailyCumulativeCard Component
 * 日次累積搬入量を表示するカード
 */

import React, { useState } from 'react';
import { Card, Typography, Space, Switch } from 'antd';
import { InfoTooltip } from '@/features/dashboard/ukeire/shared/ui/InfoTooltip';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RTooltip,
  Legend,
  Line,
} from 'recharts';
import { COLORS, FONT } from '@/features/dashboard/ukeire/domain/constants';
import { ChartFrame } from '@/features/dashboard/ukeire/shared/ui/ChartFrame';
import { SingleLineLegend } from '@/features/dashboard/ukeire/shared/ui/SingleLineLegend';
import dayjs from 'dayjs';

export type DailyCumulativeCardProps = {
  cumData: {
    label: string;
    yyyyMMdd: string;
    actualCumulative: number;
    prevMonthCumulative: number;
    prevYearCumulative: number;
  }[];
  variant?: 'standalone' | 'embed';
};

export const DailyCumulativeCard: React.FC<DailyCumulativeCardProps> = ({
  cumData,
  variant = 'standalone',
}) => {
  const [showPrevMonth, setShowPrevMonth] = useState(false);
  const [showPrevYear, setShowPrevYear] = useState(false);

  // カスタムTooltip: すべての値を表示（実績、先月、前年）
  const CustomTooltip = ({
    active,
    payload,
    label,
  }: {
    active?: boolean;
    payload?: Array<{ payload: unknown }>;
    label?: string;
  }) => {
    if (!active || !payload || payload.length === 0) return null;

    // payloadから各値を取得
    const data = payload[0]?.payload as
      | {
          label: string;
          yyyyMMdd?: string;
          actualCumulative?: number;
          prevMonthCumulative?: number;
          prevYearCumulative?: number;
        }
      | undefined;

    if (!data) return null;

    const actual = data.actualCumulative ?? 0;
    const prevMonth = data.prevMonthCumulative ?? 0;
    const prevYear = data.prevYearCumulative ?? 0;

    // 差分計算
    const prevMonthDiff = actual !== 0 ? ((prevMonth - actual) / actual) * 100 : 0;
    const prevYearDiff = actual !== 0 ? ((prevYear - actual) / actual) * 100 : 0;

    const formatDiff = (diff: number) => {
      const sign = diff >= 0 ? '+' : '-';
      const absPct = Math.abs(diff).toFixed(1);
      return `(${sign}${absPct}%)`;
    };

    const weekday = data?.yyyyMMdd
      ? ['日', '月', '火', '水', '木', '金', '土'][dayjs(data.yyyyMMdd).day()]
      : null;
    const baseLabel = label ? `${label}日` : '';
    const labelText = baseLabel ? `${baseLabel}${weekday ? ` (${weekday})` : ''}` : '';

    return (
      <div
        style={{
          backgroundColor: 'rgba(255, 255, 255, 0.96)',
          border: '1px solid #ccc',
          padding: '8px 10px',
          fontSize: FONT.size,
          borderRadius: 4,
        }}
      >
        <div style={{ fontWeight: 600, marginBottom: 4, color: '#262626' }}>{labelText}</div>
        <div style={{ color: COLORS.actual, marginBottom: 2 }}>累積実績: {actual.toFixed(1)}t</div>
        {showPrevMonth && (
          <div style={{ color: '#40a9ff', marginBottom: 2 }}>
            先月: {prevMonth.toFixed(1)}t {formatDiff(prevMonthDiff)}
          </div>
        )}
        {showPrevYear && (
          <div style={{ color: '#fa8c16' }}>
            前年: {prevYear.toFixed(1)}t {formatDiff(prevYearDiff)}
          </div>
        )}
      </div>
    );
  };

  const Inner = () => (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        minHeight: 0,
      }}
    >
      <Space
        align="baseline"
        style={{
          justifyContent: 'space-between',
          width: '100%',
          paddingBottom: 4,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <Typography.Title level={5} style={{ margin: 0, fontSize: 13 }}>
            日次累積搬入量
          </Typography.Title>
          <InfoTooltip />
        </div>
        <Space size="small">
          <span style={{ color: '#8c8c8c' }}>先月</span>
          <Switch size="small" checked={showPrevMonth} onChange={setShowPrevMonth} />
          <span style={{ color: '#8c8c8c' }}>前年</span>
          <Switch size="small" checked={showPrevYear} onChange={setShowPrevYear} />
        </Space>
      </Space>

      <div style={{ flex: 1, minHeight: 0 }}>
        <ChartFrame style={{ flex: 1, minHeight: 0 }}>
          <AreaChart data={cumData} margin={{ left: 0, right: 8, top: 6, bottom: 12 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="label"
              tickFormatter={(v) => {
                const n = Number(String(v));
                if (Number.isNaN(n)) return String(v);
                // 奇数のみ表示
                return n % 2 === 1 ? String(v) : '';
              }}
              fontSize={FONT.size}
            />
            <YAxis unit="t" domain={[0, 'auto']} fontSize={FONT.size} />
            <RTooltip content={<CustomTooltip />} />
            <Area
              type="monotone"
              dataKey="actualCumulative"
              name="累積実績"
              stroke={COLORS.actual}
              fill={COLORS.actual}
              fillOpacity={0.2}
            />
            {showPrevMonth && (
              <Line
                type="monotone"
                dataKey="prevMonthCumulative"
                name="先月"
                stroke="#40a9ff"
                dot={false}
                strokeWidth={2}
              />
            )}
            {showPrevYear && (
              <Line
                type="monotone"
                dataKey="prevYearCumulative"
                name="前年"
                stroke="#fa8c16"
                dot={false}
                strokeWidth={2}
              />
            )}
            <Legend
              content={(props: unknown) => (
                <SingleLineLegend {...(props as Parameters<typeof SingleLineLegend>[0])} />
              )}
              verticalAlign="bottom"
            />
          </AreaChart>
        </ChartFrame>
      </div>
    </div>
  );

  if (variant === 'embed') return <Inner />;
  return (
    <Card
      variant="outlined"
      styles={{
        body: {
          padding: 12,
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          minHeight: 0,
        },
      }}
    >
      <Inner />
    </Card>
  );
};
