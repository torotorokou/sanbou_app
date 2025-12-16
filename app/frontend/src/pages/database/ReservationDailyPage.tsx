/**
 * ReservationDailyPage - 予約表（手入力）画面
 * 
 * 責務: レイアウト・配置のみ
 * ロジック: ViewModel に委譲
 */

import React from 'react';
import { Typography, Col, Row } from 'antd';
import styles from './DatasetImportPage.module.css';
import {
  useReservationDailyViewModel,
  ReservationCalendar,
  ReservationForm,
} from '@features/reservation-daily';

const { Title } = Typography;

const ReservationDailyPage: React.FC = () => {
  const vm = useReservationDailyViewModel();

  // 選択日のデータがmanualかどうか
  const selectedDateData = vm.forecastData.find(d => d.date === vm.selectedDate);
  const hasManualData = selectedDateData?.source === 'manual';

  return (
    <Row className={styles.pageContainer}>
      {/* 左カラム：手入力フォーム */}
      <Col span={10} className={styles.leftCol}>
        <Title level={4} style={{ margin: '0 0 12px 0' }}>
          予約表（手入力）
        </Title>

        <ReservationForm
          selectedDate={vm.selectedDate}
          totalTrucks={vm.totalTrucks}
          fixedTrucks={vm.fixedTrucks}
          note={vm.note}
          onChangeTotalTrucks={vm.onChangeTotalTrucks}
          onChangeFixedTrucks={vm.onChangeFixedTrucks}
          onChangeNote={vm.onChangeNote}
          onSubmit={vm.onSubmit}
          onDelete={vm.onDelete}
          isSaving={vm.isSaving}
          error={vm.error}
          successMessage={vm.successMessage}
          hasManualData={hasManualData}
        />

        <div style={{ 
          padding: '12px', 
          background: '#f5f5f5', 
          borderRadius: 4,
          fontSize: 12,
        }}>
          <Typography.Text type="secondary">
            <strong>使い方</strong><br />
            1. カレンダーから日付を選択<br />
            2. 台数を入力して保存<br />
            3. カレンダーに即反映されます
          </Typography.Text>
        </div>
      </Col>

      {/* 右カラム：カレンダー表示 */}
      <Col span={14} className={styles.rightCol}>
        <ReservationCalendar
          currentMonth={vm.currentMonth}
          forecastData={vm.forecastData}
          selectedDate={vm.selectedDate}
          onChangeMonth={vm.onChangeMonth}
          onSelectDate={vm.onSelectDate}
          isLoading={vm.isLoading}
        />
      </Col>
    </Row>
  );
};

export default ReservationDailyPage;
