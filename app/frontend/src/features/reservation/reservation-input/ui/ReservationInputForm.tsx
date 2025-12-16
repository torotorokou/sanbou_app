/**
 * ReservationInputForm - 予約手入力フォーム
 * 
 * UI Component (状態レス)
 * 規約: Named Export を使用
 */

import React from 'react';
import { Form, InputNumber, Input, Button, Space, Alert, Typography, Card, DatePicker, message } from 'antd';
import { SaveOutlined, DeleteOutlined, CalendarOutlined } from '@ant-design/icons';
import type { Dayjs } from 'dayjs';

const { Title, Text } = Typography;
const { TextArea } = Input;

interface ReservationInputFormProps {
  selectedDate: Dayjs | null;
  totalTrucks: number | null;
  fixedTrucks: number | null;
  note: string;
  onSelectDate: (date: Dayjs | null) => void;
  onChangeTotalTrucks: (value: number | null) => void;
  onChangeFixedTrucks: (value: number | null) => void;
  onChangeNote: (value: string) => void;
  onSubmit: () => void;
  onDelete: () => void;
  isSaving: boolean;
  error: string | null;
  hasManualData: boolean;
}

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
  const handleDateChange = (date: Dayjs | null) => {
    onSelectDate(date);
  };

  const handleSubmit = async () => {
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
    
    await onSubmit();
  };

  const isFormDisabled = isSaving;

  return (
    <Card 
      size="small" 
      style={{ marginBottom: 16 }}
      styles={{ body: { padding: '12px 16px' } }}
    >
      <Title level={5} style={{ margin: '0 0 12px 0', fontSize: 16 }}>
        📝 予約データ入力
      </Title>

      {error && (
        <Alert
          message={error}
          type="error"
          showIcon
          closable
          style={{ marginBottom: 12 }}
        />
      )}

      <Form layout="vertical" size="small">
        <Form.Item 
          label="入力日"
          required
          style={{ marginBottom: 8 }}
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
          style={{ marginBottom: 8 }}
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
          style={{ marginBottom: 8 }}
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

        <Form.Item label="備考（任意）" style={{ marginBottom: 12 }}>
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
            style={{ marginBottom: 12 }}
          />
        )}

        <Space style={{ width: '100%' }} direction="vertical" size={8}>
          <Button
            type="primary"
            icon={<SaveOutlined />}
            onClick={handleSubmit}
            disabled={isFormDisabled}
            loading={isSaving}
            block
          >
            保存
          </Button>

          {hasManualData && selectedDate && (
            <Button
              danger
              icon={<DeleteOutlined />}
              onClick={onDelete}
              disabled={isFormDisabled}
              loading={isSaving}
              block
            >
              削除
            </Button>
          )}
        </Space>
      </Form>

      <div style={{ marginTop: 12, padding: '10px', background: '#f9f9f9', borderRadius: 4, fontSize: 13 }}>
        <Text type="secondary">
          ※ 固定客台数は合計台数以下である必要があります
        </Text>
      </div>
    </Card>
  );
};
