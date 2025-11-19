/**
 * アップロードカレンダー
 * CSV アップロード状況を月間カレンダー形式で表示
 */

import React, { useState } from 'react';
import { Card, Button, Space, Typography, Spin, Alert } from 'antd';
import { LeftOutlined, RightOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { useUploadCalendar } from '../model/useUploadCalendar';
import { UploadDetailModal } from './UploadDetailModal';
import { UploadCalendarLegend } from './UploadCalendarLegend';
import { getCsvUploadKindMaster, getKindsByDatasetKey, getMasterByDatasetKey, type CsvUploadKind } from '../model/types';
import type { CalendarDay } from '../model/types';

const { Title, Text } = Typography;

const WEEKDAYS = ['日', '月', '火', '水', '木', '金', '土'];

interface UploadCalendarProps {
  datasetKey?: string; // 選択中のデータセットキー
}

export const UploadCalendar: React.FC<UploadCalendarProps> = ({ datasetKey = 'shogun_flash' }) => {
  const {
    currentMonth,
    weeks,
    isLoading,
    error,
    goPrevMonth,
    goNextMonth,
    deleteUpload,
  } = useUploadCalendar();

  const [selectedDay, setSelectedDay] = useState<CalendarDay | null>(null);
  const [modalOpen, setModalOpen] = useState(false);

  // 選択中のデータセットに応じたCSV種別を取得
  const allowedKinds = getKindsByDatasetKey(datasetKey);
  // 凡例に合わせたマスタ順で描画するための配列
  const masters = getMasterByDatasetKey(datasetKey);

  const handleDayClick = (day: CalendarDay) => {
    const uploadsCount = Object.values(day.uploadsByKind).flat().length;
    if (uploadsCount === 0) return; // アップロードがない日はクリック無効

    setSelectedDay(day);
    setModalOpen(true);
  };

  const handleModalClose = () => {
    setModalOpen(false);
    setSelectedDay(null);
  };

  // 選択中のデータセットに関連するアップロードのみを表示
  const selectedUploads = selectedDay
    ? Object.entries(selectedDay.uploadsByKind)
        .filter(([kind]) => allowedKinds.includes(kind as CsvUploadKind))
        .flatMap(([, items]) => items || [])
    : [];

  return (
    <Card
      title={
        <Space direction="vertical" size={0} style={{ width: '100%' }}>
          <Title level={5} style={{ margin: 0, fontSize: 14 }}>
            📅 アップロード状況カレンダー
          </Title>
        </Space>
      }
      size="small"
      style={{ height: '100%', display: 'flex', flexDirection: 'column' }}
      styles={{ body: { flex: 1, overflow: 'auto', padding: '12px' } }}
    >
      {/* 月移動ヘッダー */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <Button
          type="text"
          icon={<LeftOutlined />}
          onClick={goPrevMonth}
          size="small"
        />
        <Text strong style={{ fontSize: 14 }}>
          {dayjs(currentMonth).format('YYYY年MM月')}
        </Text>
        <Button
          type="text"
          icon={<RightOutlined />}
          onClick={goNextMonth}
          size="small"
        />
      </div>

      {/* ローディング・エラー表示 */}
      {isLoading && (
        <div style={{ textAlign: 'center', padding: '2rem' }}>
          <Spin />
        </div>
      )}

      {error && !isLoading && (
        <Alert message="エラー" description={error} type="error" showIcon />
      )}

      {/* カレンダー本体 */}
      {!isLoading && !error && (
        <>
          {/* 曜日ヘッダー */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 2, marginBottom: 4 }}>
                {WEEKDAYS.map((day, idx) => (
                  <div
                    key={day}
                    style={{
                      textAlign: 'center',
                      fontSize: 15,
                      fontWeight: 'bold',
                      color: idx === 0 ? '#ff4d4f' : idx === 6 ? '#1890ff' : '#595959',
                      padding: '8px 0',
                    }}
                  >
                    {day}
                  </div>
                ))}
          </div>

          {/* 週ごとのグリッド */}
          {weeks.map((week, weekIdx) => (
            <div key={weekIdx} style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 2, marginBottom: 2 }}>
              {week.days.map((day, dayIdx) => {
                const dayOfMonth = dayjs(day.date).date();
                // 選択中のデータセットに関連するアップロードのみをカウント
                const filteredUploads = Object.entries(day.uploadsByKind)
                  .filter(([kind]) => allowedKinds.includes(kind as CsvUploadKind))
                  .flatMap(([, items]) => items || []);
                const uploadsCount = filteredUploads.length;
                const hasUploads = uploadsCount > 0;
                
                // 今日かどうかを判定
                const isToday = dayjs(day.date).isSame(dayjs(), 'day');

                return (
                  <div
                    key={day.date}
                    onClick={() => handleDayClick(day)}
                    style={{
                      minHeight: 96,
                      border: '1px solid #d9d9d9',
                      borderRadius: 4,
                      padding: 6,
                      backgroundColor: isToday 
                        ? '#fffbe6'  // 今日は黄色
                        : day.isCurrentMonth 
                        ? (hasUploads ? '#fafafa' : '#fff') 
                        : '#f5f5f5',
                      cursor: hasUploads ? 'pointer' : 'default',
                      position: 'relative',
                      transition: 'all 0.2s',
                      ...(hasUploads && {
                        ':hover': {
                          backgroundColor: '#e6f7ff',
                          borderColor: '#1890ff',
                        },
                      }),
                    }}
                    onMouseEnter={(e) => {
                      if (hasUploads) {
                        e.currentTarget.style.backgroundColor = '#e6f7ff';
                        e.currentTarget.style.borderColor = '#1890ff';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (hasUploads) {
                        e.currentTarget.style.backgroundColor = isToday
                          ? '#fffbe6'
                          : day.isCurrentMonth ? '#fafafa' : '#f5f5f5';
                        e.currentTarget.style.borderColor = '#d9d9d9';
                      }
                    }}
                  >
                    {/* 日付 */}
                    <div
                      style={{
                        fontSize: 16,
                        color: !day.isCurrentMonth
                          ? '#bfbfbf'
                          : isToday
                          ? '#faad14'  // 今日はオレンジ色
                          : dayIdx === 0
                          ? '#ff4d4f'
                          : dayIdx === 6
                          ? '#1890ff'
                          : '#595959',
                        fontWeight: day.isCurrentMonth ? 'bold' : 'normal',
                        marginBottom: 4,
                      }}
                    >
                      {dayOfMonth}
                    </div>

                    {/* アップロード状況ドット */}
                        {/* 凡例と合わせた丸（アップロード未実施は点線の透明丸） */}
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                          {masters.map((master) => {
                            // この日の該当種別アップロード有無を判定
                            const items = day.uploadsByKind[master.kind];
                            const has = !!(items && items.length > 0);
                            return (
                              <span
                                key={master.kind}
                                title={master.label}
                                style={{
                                  display: 'inline-block',
                                  width: 14,
                                  height: 14,
                                  borderRadius: '50%',
                                  boxSizing: 'border-box',
                                  ...(has
                                    ? { backgroundColor: master.color }
                                    : {
                                        backgroundColor: 'transparent',
                                        border: '2px dashed rgba(0,0,0,0.12)',
                                      }),
                                }}
                              />
                            );
                          })}
                        </div>
                  </div>
                );
              })}
            </div>
          ))}

          {/* 凡例 */}
          <UploadCalendarLegend datasetKey={datasetKey} />
        </>
      )}

      {/* 詳細モーダル */}
      {selectedDay && (
        <UploadDetailModal
          date={selectedDay.date}
          uploads={selectedUploads}
          open={modalOpen}
          onClose={handleModalClose}
          onDelete={deleteUpload}
        />
      )}
    </Card>
  );
};
