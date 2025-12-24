/**
 * ReservationDailyPage - 予約表（手入力）画面
 * 
 * Controller (ページコンポーネント)
 * 
 * 責務:
 * - レイアウト・配置のみ
 * - 複数のfeatureを組み合わせて画面を構成
 * - ViewModelの初期化と画面間の連携
 * 
 * 構成:
 * - 左カラム: 日付選択カレンダー + 手入力フォーム（独立した入力UI）
 * - 右カラム: 履歴カレンダー（ログ表示専用、左と連動しない）
 * 
 * 規約:
 * - Feature-Sliced Design (FSD) に準拠
 * - ビジネスロジックは ViewModel に委譲
 * - 明示的な Named Export を使用
 */

import React, { useState, useEffect } from 'react';
import { Typography, Col, Row, Collapse, Card } from 'antd';
import styles from './ReservationDailyPage.module.css';
import { useReservationInputVM, ReservationInputForm } from '@features/reservation/reservation-input';
import { 
  useReservationCalendarVM, 
  ReservationHistoryCalendar,
  ReservationMonthlyStats,
  ReservationMonthlyChart
} from '@features/reservation/reservation-calendar';
import { UnimplementedModal } from '@features/unimplemented-feature';

const { Title } = Typography;

const ReservationDailyPage: React.FC = () => {
  // 未実装モーダル用の状態
  const [showUnimplementedModal, setShowUnimplementedModal] = useState(false);

  // ページ読み込み時にモーダルを表示（テスト用）
  useEffect(() => {
    setShowUnimplementedModal(true);
  }, []);
  
  // カレンダー表示用ViewModel
  const calendarVM = useReservationCalendarVM();
  
  // 手入力フォーム用ViewModel（データ変更時にカレンダーを更新）
  const inputVM = useReservationInputVM(undefined, () => {
    calendarVM.refreshData();
  });

  return (
    <>
      <Title level={4} style={{ margin: '0 0 8px 0', textAlign: 'center' }}>
        予約表
      </Title>
      
      <Row className={styles.pageContainer}>
        {/* 左カラム：手入力フォーム */}
        <Col span={10} className={styles.leftCol}>
          <Collapse
          size="small"
          style={{ marginBottom: 8 }}
          items={[
            {
              key: '1',
              label: <strong>📖 使い方</strong>,
              children: (
                <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                  1. 下のカレンダーから日付を選択<br />
                  2. 合計台数・固定客台数を入力して保存<br />
                  3. 右の履歴カレンダーに即反映されます<br />
                  <br />
                  <strong>注意:</strong><br />
                  ・ 備考欄は任意（空欄OK）<br />
                  ・ 固定客台数は合計台数以下である必要があります<br />
                  ・ 右のカレンダーの任意の日付をクリックで削除できます
                </Typography.Text>
              ),
            },
          ]}
        />

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

        {/* 月次統計と日別予約推移 */}
        <Card
          size="small"
          className={styles.statsCard}
          styles={{ body: { padding: '8px 12px', height: '100%', display: 'flex', flexDirection: 'column', overflow: 'auto' } }}
        >
          <ReservationMonthlyStats
            data={calendarVM.historyData}
            isLoading={calendarVM.isLoadingHistory}
          />
          
          <ReservationMonthlyChart
            data={calendarVM.historyData}
            isLoading={calendarVM.isLoadingHistory}
          />
        </Card>
      </Col>

      {/* 右カラム：履歴カレンダー（ログ表示専用） */}
      <Col span={14} className={styles.rightCol}>
        <ReservationHistoryCalendar
          historyMonth={calendarVM.historyMonth}
          historyData={calendarVM.historyData}
          onChangeHistoryMonth={calendarVM.onChangeHistoryMonth}
          onDeleteDate={calendarVM.onDeleteDate}
          goToCurrentMonth={calendarVM.goToCurrentMonth}
          isLoadingHistory={calendarVM.isLoadingHistory}
          isDeletingDate={calendarVM.isDeletingDate}
        />
      </Col>
    </Row>
    
    {/* 未実装モーダル */}
    <UnimplementedModal
      visible={showUnimplementedModal}
      onClose={() => setShowUnimplementedModal(false)}
      featureName="予約表"
      description="この機能は現在開発中です。近日中にリリース予定ですので、今しばらくお待ちください。"
    />
    </>
  );
};

export default ReservationDailyPage;
