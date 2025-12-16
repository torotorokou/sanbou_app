/**
 * ReservationMonthlyChart - 月次予約棒グラフ
 * 
 * UI Component (状態レス)
 * 日別の予約台数を棒グラフで表示
 */

import React, { useMemo } from 'react';
import type { ReservationForecastDaily } from '../../shared';

interface ReservationMonthlyChartProps {
  data: ReservationForecastDaily[];
  isLoading?: boolean;
}

export const ReservationMonthlyChart: React.FC<ReservationMonthlyChartProps> = ({
  data,
  isLoading = false,
}) => {
  // 月の全日データを生成（データがない日は0で補完）
  const fullMonthData = useMemo(() => {
    if (data.length === 0) return [];
    
    // dataから年月を取得
    const firstDate = new Date(data[0].date);
    const year = firstDate.getFullYear();
    const month = firstDate.getMonth();
    
    // その月の最終日を取得
    const lastDay = new Date(year, month + 1, 0).getDate();
    
    // dataをMapに変換（高速検索用）
    const dataMap = new Map(data.map(d => [d.date, d]));
    
    // 1日から最終日までの配列を生成
    const fullData = [];
    for (let day = 1; day <= lastDay; day++) {
      const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
      const existingData = dataMap.get(dateStr);
      
      fullData.push(existingData || {
        date: dateStr,
        reserve_trucks: 0,
        reserve_fixed_trucks: 0
      });
    }
    
    return fullData;
  }, [data]);

  // 最大値を計算してスケーリング
  const maxValue = useMemo(() => {
    const max = Math.max(...data.map(d => d.reserve_trucks), 0);
    return max > 0 ? max : 100; // 最小値を100に設定
  }, [data]);

  return (
    <div style={{ marginTop: 20 }}>
      <style>{`
        .chart-bar:hover .chart-value {
          opacity: 1 !important;
        }
      `}</style>
      {isLoading ? (
        <div style={{ textAlign: 'center', padding: '40px 0', color: '#999' }}>
          読み込み中...
        </div>
      ) : fullMonthData.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '40px 0', color: '#999' }}>
          データがありません
        </div>
      ) : (
        <div style={{ 
          display: 'flex', 
          alignItems: 'flex-end', 
          height: 100, 
          gap: 2,
          padding: '5px 0',
          borderBottom: '2px solid #e0e0e0'
        }}>
          {fullMonthData.map((item) => {
            const date = new Date(item.date);
            const day = date.getDate();
            const totalHeight = (item.reserve_trucks / maxValue) * 90;
            const fixedHeight = (item.reserve_fixed_trucks / maxValue) * 90;

            return (
              <div
                key={item.date}
                style={{
                  flex: 1,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  minWidth: 0,
                  position: 'relative',
                }}
              >
                {/* 棒グラフ */}
                <div
                  className="chart-bar"
                  style={{
                    width: '100%',
                    height: totalHeight,
                    background: `linear-gradient(to top, #52c41a ${(fixedHeight / totalHeight) * 100}%, #1890ff ${(fixedHeight / totalHeight) * 100}%)`,
                    borderRadius: '2px 2px 0 0',
                    position: 'relative',
                    minHeight: item.reserve_trucks > 0 ? 5 : 0,
                    cursor: 'pointer',
                  }}
                >
                  {/* 値表示（ホバー時のみ） */}
                  {totalHeight > 0 && (
                    <div
                      className="chart-value"
                      style={{
                        position: 'absolute',
                        top: -20,
                        left: '50%',
                        transform: 'translateX(-50%)',
                        fontSize: 10,
                        fontWeight: 'bold',
                        color: '#333',
                        whiteSpace: 'nowrap',
                        opacity: 0,
                        transition: 'opacity 0.2s',
                        pointerEvents: 'none',
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
      {fullMonthData.length > 0 && (
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
    </div>
  );
};
