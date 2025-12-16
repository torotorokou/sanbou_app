/**
 * ReservationForm - 予約手入力フォーム
 * 
 * UI Component
 */

import React from 'react';
import { Form, InputNumber, Input, Button, Space, Alert, Typography, Card } from 'antd';
import { SaveOutlined, DeleteOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { TextArea } = Input;

interface ReservationFormProps {
  selectedDate: string | null;
  totalTrucks: number;
  fixedTrucks: number;
  note: string;
  onChangeTotalTrucks: (value: number) => void;
  onChangeFixedTrucks: (value: number) => void;
  onChangeNote: (value: string) => void;
  onSubmit: () => void;
  onDelete: () => void;
  isSaving: boolean;
  error: string | null;
  successMessage: string | null;
  hasManualData: boolean;
}

export const ReservationForm: React.FC<ReservationFormProps> = ({
  selectedDate,
  totalTrucks,
  fixedTrucks,
  note,
  onChangeTotalTrucks,
  onChangeFixedTrucks,
  onChangeNote,
  onSubmit,
  onDelete,
  isSaving,
  error,
  successMessage,
  hasManualData,
}) => {
  const isFormDisabled = !selectedDate || isSaving;

  return (
    <Card 
      size="small" 
      style={{ marginBottom: 16 }}
      styles={{ body: { padding: '12px 16px' } }}
    >
      <Title level={5} style={{ margin: '0 0 12px 0', fontSize: 14 }}>
        📝 予約データ入力
      </Title>

      {selectedDate && (
        <div style={{ marginBottom: 12, padding: '8px', background: '#f5f5f5', borderRadius: 4 }}>
          <Text strong>選択日: </Text>
          <Text>{dayjs(selectedDate).format('YYYY年MM月DD日')}</Text>
        </div>
      )}

      {!selectedDate && (
        <Alert 
          message="カレンダーから日付を選択してください" 
          type="info" 
          showIcon 
          style={{ marginBottom: 12 }}
        />
      )}

      <Form layout="vertical" size="small">
        <Form.Item label="合計台数" style={{ marginBottom: 8 }}>
          <InputNumber
            value={totalTrucks}
            onChange={(v) => onChangeTotalTrucks(v ?? 0)}
            min={0}
            disabled={isFormDisabled}
            style={{ width: '100%' }}
            placeholder="0"
          />
        </Form.Item>

        <Form.Item label="固定客台数" style={{ marginBottom: 8 }}>
          <InputNumber
            value={fixedTrucks}
            onChange={(v) => onChangeFixedTrucks(v ?? 0)}
            min={0}
            max={totalTrucks}
            disabled={isFormDisabled}
            style={{ width: '100%' }}
            placeholder="0"
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

        {successMessage && (
          <Alert
            message={successMessage}
            type="success"
            showIcon
            closable
            style={{ marginBottom: 12 }}
          />
        )}

        <Space style={{ width: '100%' }} direction="vertical" size={8}>
          <Button
            type="primary"
            icon={<SaveOutlined />}
            onClick={onSubmit}
            disabled={isFormDisabled}
            loading={isSaving}
            block
          >
            保存
          </Button>

          {hasManualData && (
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

      <div style={{ marginTop: 12, padding: '8px', background: '#f9f9f9', borderRadius: 4, fontSize: 11 }}>
        <Text type="secondary">
          ※ 固定客台数は合計台数以下である必要があります
        </Text>
      </div>
    </Card>
  );
};
