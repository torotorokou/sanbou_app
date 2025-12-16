/**
 * ReservationInputForm - 予約手入力フォーム
 * 
 * UI Component (状態レス)
 * 規約: Named Export を使用
 */

import React, { useState } from 'react';
import { Form, InputNumber, Input, Button, Space, Alert, Typography, Card, DatePicker, message, Modal } from 'antd';
import { SaveOutlined, CalendarOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import type { ReservationInputFormProps } from '../model/types';

const { Title } = Typography;
const { TextArea } = Input;

export const ReservationInputForm: React.FC<ReservationInputFormProps> = ({
  selectedDate,
  totalTrucks,
  fixedTrucks,
  note,
  onSelectDate,
  onChangeTotalTrucks,
  onChangeFixedTrucks,
  onChangeNote,
  onSubmit,
  onDelete,
  isSaving,
  error,
  hasManualData,
}) => {
  const [isConfirmModalOpen, setIsConfirmModalOpen] = useState(false);

  const handleDateChange = (date: Dayjs | null) => {
    onSelectDate(date);
  };

  const handleSaveClick = () => {
    // バリデーション（note以外が空欄の場合）
    if (!selectedDate) {
      message.error('日付を選択してください');
      return;
    }
    if (totalTrucks === null || totalTrucks === undefined) {
      message.error('総台数を入力してください');
      return;
    }
    if (fixedTrucks === null || fixedTrucks === undefined) {
      message.error('固定客数を入力してください');
      return;
    }
    
    // 確認モーダルを表示
    setIsConfirmModalOpen(true);
  };

  const handleConfirmSave = async () => {
    setIsConfirmModalOpen(false);
    await onSubmit();
  };

  const isFormDisabled = isSaving;

  return (
    <Card 
      size="small" 
      style={{ marginBottom: 8 }}
      styles={{ body: { padding: '8px 12px' } }}
    >
      <Title level={5} style={{ margin: '0 0 8px 0', fontSize: 16 }}>
        📝 予約データ入力
      </Title>

      {error && (
        <Alert
          message={error}
          type="error"
          showIcon
          closable
          style={{ marginBottom: 8 }}
        />
      )}

      <Form layout="vertical" size="small">
        <Form.Item 
          label="入力日"
          required
          style={{ marginBottom: 6 }}
        >
          <DatePicker
            value={selectedDate}
            onChange={handleDateChange}
            format="YYYY-MM-DD (dd)"
            placeholder="日付を選択"
            style={{ width: '100%', fontSize: '16px' }}
            suffixIcon={<CalendarOutlined style={{ fontSize: '18px' }} />}
            disabled={isFormDisabled}
          />
        </Form.Item>

        <Form.Item 
          label="合計台数" 
          required
          style={{ marginBottom: 6 }}
        >
          <InputNumber
            value={totalTrucks}
            onChange={onChangeTotalTrucks}
            min={0}
            disabled={isFormDisabled}
            style={{ width: '100%' }}
            placeholder="例: 12"
          />
        </Form.Item>

        <Form.Item 
          label="固定客台数" 
          required
          style={{ marginBottom: 6 }}
        >
          <InputNumber
            value={fixedTrucks}
            onChange={onChangeFixedTrucks}
            min={0}
            max={totalTrucks ?? undefined}
            disabled={isFormDisabled}
            style={{ width: '100%' }}
            placeholder="例: 3"
          />
        </Form.Item>

        <Form.Item label="備考（任意）" style={{ marginBottom: 8 }}>
          <TextArea
            value={note}
            onChange={(e) => onChangeNote(e.target.value)}
            disabled={isFormDisabled}
            rows={2}
            placeholder="メモを入力..."
          />
        </Form.Item>

        {error && (
          <Alert
            message={error}
            type="error"
            showIcon
            closable
            style={{ marginBottom: 8 }}
          />
        )}

        <Button
          type="primary"
          icon={<SaveOutlined />}
          onClick={handleSaveClick}
          disabled={isFormDisabled}
          loading={isSaving}
          block
        >
          保存
        </Button>
      </Form>

      {/* 保存確認モーダル */}
      <Modal
        title={<span><ExclamationCircleOutlined style={{ color: '#faad14', marginRight: 8 }} />保存確認</span>}
        open={isConfirmModalOpen}
        onOk={handleConfirmSave}
        onCancel={() => setIsConfirmModalOpen(false)}
        okText="保存する"
        cancelText="キャンセル"
        okButtonProps={{ loading: isSaving }}
      >
        <p>以下の内容で保存してもよろしいですか？</p>
        <div style={{ background: '#f5f5f5', padding: 12, borderRadius: 4, marginTop: 12 }}>
          <p style={{ margin: '4px 0' }}><strong>日付:</strong> {selectedDate?.format('YYYY年MM月DD日 (dd)')}</p>
          <p style={{ margin: '4px 0' }}><strong>合計台数:</strong> {totalTrucks}台</p>
          <p style={{ margin: '4px 0' }}><strong>固定客台数:</strong> {fixedTrucks}台</p>
          {note && <p style={{ margin: '4px 0' }}><strong>備考:</strong> {note}</p>}
        </div>
      </Modal>
    </Card>
  );
};
