/**
 * ReservationDailyPage - 予約表（手入力）画面
 * 
 * 責務: レイアウト・配置のみ
 * ロジック: ViewModel に委譲
 */

import React from 'react';
import { Typography, Col, Row } from 'antd';
import styles from './DatasetImportPage.module.css';

const { Title } = Typography;

const ReservationDailyPage: React.FC = () => {
  return (
    <Row className={styles.pageContainer}>
      {/* 左カラム：手入力フォーム */}
      <Col span={10} className={styles.leftCol}>
        <Title level={4}>予約表（手入力）</Title>
        <div style={{ padding: '16px', border: '1px dashed #d9d9d9', borderRadius: 4 }}>
          <p>フォーム実装予定エリア</p>
          <ul>
            <li>予約日</li>
            <li>合計台数</li>
            <li>固定客台数</li>
          </ul>
        </div>
      </Col>

      {/* 右カラム：カレンダー表示 */}
      <Col span={14} className={styles.rightCol}>
        <div style={{ padding: '16px', border: '1px dashed #d9d9d9', borderRadius: 4 }}>
          <p>カレンダー実装予定エリア</p>
        </div>
      </Col>
    </Row>
  );
};

export default ReservationDailyPage;
