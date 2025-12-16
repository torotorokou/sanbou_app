/**
 * ReservationDailyPage - 予約表（手入力）画面
 * 
 * 責務: レイアウト・配置のみ
 * ロジック: ViewModel に委譲
 * 
 * 構成:
 * - 左カラム: 日付選択カレンダー + 手入力フォーム（独立した入力UI）
 * - 右カラム: 履歴カレンダー（ログ表示専用、左と連動しない）
 * 
 * 規約: 機能ごとに分割されたfeatureを組み合わせて使用
 */

import React from 'react';
import { Typography, Col, Row } from 'antd';
import styles from './DatasetImportPage.module.css';
import { useReservationInputVM, ReservationInputForm } from '@features/reservation/reservation-input';
import { 
  useReservationCalendarVM, 
  ReservationHistoryCalendar,
  ReservationMonthlyStats 
} from '@features/reservation/reservation-calendar';

const { Title } = Typography;

const ReservationDailyPage: React.FC = () => {
  // カレンダー表示用ViewModel
  const calendarVM = useReservationCalendarVM();
  
  // 手入力フォーム用ViewModel（データ変更時にカレンダーを更新）
  const inputVM = useReservationInputVM(undefined, () => {
    calendarVM.refreshData();
  });

  return (
    <Row className={styles.pageContainer}>
      {/* 左カラム：手入力フォーム */}
      <Col span={10} className={styles.leftCol}>
        <Title level={4} style={{ margin: '0 0 12px 0' }}>
          予約表（手入力）
        </Title>

        <ReservationInputForm
          selectedDate={inputVM.selectedDate}
          totalTrucks={inputVM.totalTrucks}
          fixedTrucks={inputVM.fixedTrucks}
          note={inputVM.note}
          onSelectDate={inputVM.onSelectDate}
          onChangeTotalTrucks={inputVM.onChangeTotalTrucks}
          onChangeFixedTrucks={inputVM.onChangeFixedTrucks}
          onChangeNote={inputVM.onChangeNote}
          onSubmit={inputVM.onSubmit}
          onDelete={inputVM.onDelete}
          isSaving={inputVM.isSaving}
          error={inputVM.error}
          hasManualData={inputVM.hasManualData}
        />

        <div style={{ 
          padding: '12px', 
          background: '#f5f5f5', 
          borderRadius: 4,
          fontSize: 13,
        }}>
          <Typography.Text type="secondary">
            <strong>使い方</strong><br />
            1. 上のカレンダーから日付を選択<br />
            2. 合計台数・固定客台数を入力して保存<br />
            3. 右の履歴カレンダーに即反映されます<br />
            ※ 備考欄は任意（空欄OK）
          </Typography.Text>
        </div>
      </Col>

      {/* 右カラム：履歴カレンダー（ログ表示専用） */}
      <Col span={14} className={styles.rightCol}>
        <ReservationHistoryCalendar
          historyMonth={calendarVM.historyMonth}
          historyData={calendarVM.historyData}
          onChangeHistoryMonth={calendarVM.onChangeHistoryMonth}
          isLoadingHistory={calendarVM.isLoadingHistory}
        />
        
        {/* 月次統計グラフ */}
        <ReservationMonthlyStats
          data={calendarVM.historyData}
          isLoading={calendarVM.isLoadingHistory}
        />
      </Col>
    </Row>
  );
};

export default ReservationDailyPage;
