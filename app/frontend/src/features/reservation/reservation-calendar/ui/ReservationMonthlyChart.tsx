/**
 * ReservationMonthlyChart - 月次予約棒グラフ
 * 
 * UI Component (状態レス)
 * 日別の予約台数を棒グラフで表示
 */

import React, { useMemo } from 'react';
import { Card, Typography } from 'antd';
import type { ReservationForecastDaily } from '../../shared';

const { Text } = Typography;

interface ReservationMonthlyChartProps {
  data: ReservationForecastDaily[];
  isLoading?: boolean;
}

export const ReservationMonthlyChart: React.FC<ReservationMonthlyChartProps> = ({
  data,
  isLoading = false,
}) => {
  // 最大値を計算してスケーリング
  const maxValue = useMemo(() => {
    const max = Math.max(...data.map(d => d.reserve_trucks), 0);
    return max > 0 ? max : 100; // 最小値を100に設定
  }, [data]);

  // 日付順にソート
  const sortedData = useMemo(() => {
    return [...data].sort((a, b) => a.date.localeCompare(b.date));
  }, [data]);

  return (
    <Card
      size="small"
      style={{ marginTop: 16 }}
      styles={{ body: { padding: '16px' } }}
    >
      <div style={{ marginBottom: 12 }}>
        <Text strong style={{ fontSize: 14 }}>📈 日別予約推移</Text>
      </div>

      {isLoading ? (
        <div style={{ textAlign: 'center', padding: '40px 0', color: '#999' }}>
          読み込み中...
        </div>
      ) : sortedData.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '40px 0', color: '#999' }}>
          データがありません
        </div>
      ) : (
        <div style={{ 
          display: 'flex', 
          alignItems: 'flex-end', 
          height: 200, 
          gap: 2,
          padding: '10px 0',
          borderBottom: '2px solid #e0e0e0'
        }}>
          {sortedData.map((item) => {
            const date = new Date(item.date);
            const day = date.getDate();
            const totalHeight = (item.reserve_trucks / maxValue) * 180;
            const fixedHeight = (item.reserve_fixed_trucks / maxValue) * 180;

            return (
              <div
                key={item.date}
                style={{
                  flex: 1,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  minWidth: 0,
                }}
              >
                {/* 棒グラフ */}
                <div
                  style={{
                    width: '100%',
                    height: totalHeight,
                    background: `linear-gradient(to top, #52c41a ${(fixedHeight / totalHeight) * 100}%, #1890ff ${(fixedHeight / totalHeight) * 100}%)`,
                    borderRadius: '2px 2px 0 0',
                    position: 'relative',
                    minHeight: item.reserve_trucks > 0 ? 5 : 0,
                    cursor: 'pointer',
                  }}
                  title={`${day}日 - 合計：${item.reserve_trucks}台 (固定：${item.reserve_fixed_trucks}台)`}
                >
                  {/* 値表示（高さが十分ある場合のみ） */}
                  {totalHeight > 30 && (
                    <div
                      style={{
                        position: 'absolute',
                        top: -20,
                        left: '50%',
                        transform: 'translateX(-50%)',
                        fontSize: 10,
                        fontWeight: 'bold',
                        color: '#333',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {item.reserve_trucks}
                    </div>
                  )}
                </div>

                {/* 日付ラベル */}
                <div
                  style={{
                    fontSize: 10,
                    color: '#666',
                    marginTop: 4,
                    textAlign: 'center',
                  }}
                >
                  {day}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* 凡例 */}
      {sortedData.length > 0 && (
        <div style={{ marginTop: 12, display: 'flex', justifyContent: 'center', gap: 16, fontSize: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <div style={{ width: 16, height: 16, background: '#1890ff', borderRadius: 2 }} />
            <span>予約台数</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <div style={{ width: 16, height: 16, background: '#52c41a', borderRadius: 2 }} />
            <span>固定客台数</span>
          </div>
        </div>
      )}
    </Card>
  );
};
