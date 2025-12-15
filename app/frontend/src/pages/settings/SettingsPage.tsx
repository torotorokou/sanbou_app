/**
 * Settings Page - 設定ページ
 * 
 * ユーザーの設定情報を表示・管理するページ。
 * 現在は認証情報（ID、ログイン名、メールアドレス、ロール）を表示。
 * 
 * 【変更履歴】
 * - AuthProviderを使用してグローバルな認証状態を参照
 */

import React from 'react';
import { Card, Descriptions, Spin, Alert, Typography, Space } from 'antd';
import { UserOutlined, MailOutlined, IdcardOutlined, SafetyOutlined } from '@ant-design/icons';
import { useAuth } from '@app/providers/AuthProvider';

const { Title } = Typography;

export const SettingsPage: React.FC = () => {
  const { user, isInitializing: isLoading, error } = useAuth();

  if (isLoading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        minHeight: '400px' 
      }}>
        <Spin size="large" tip="ユーザー情報を読み込み中..." />
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '24px' }}>
        <Alert
          message="エラー"
          description={error}
          type="error"
          showIcon
        />
      </div>
    );
  }

  if (!user) {
    return (
      <div style={{ padding: '24px' }}>
        <Alert
          message="未ログイン"
          description="ログインしていません。"
          type="warning"
          showIcon
        />
      </div>
    );
  }

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <div>
          <Title level={2}>
            <UserOutlined /> 設定
          </Title>
        </div>

        <Card title="ユーザー情報" bordered={false}>
          <Descriptions
            bordered
            column={{ xs: 1, sm: 1, md: 2 }}
            labelStyle={{ fontWeight: 'bold', width: '150px' }}
          >
            <Descriptions.Item 
              label={
                <span>
                  <IdcardOutlined style={{ marginRight: 8 }} />
                  ユーザーID
                </span>
              }
            >
              {user.userId || '(未設定)'}
            </Descriptions.Item>

            <Descriptions.Item 
              label={
                <span>
                  <UserOutlined style={{ marginRight: 8 }} />
                  ログイン名
                </span>
              }
            >
              {user.displayName || user.email.split('@')[0]}
            </Descriptions.Item>

            <Descriptions.Item 
              label={
                <span>
                  <MailOutlined style={{ marginRight: 8 }} />
                  メールアドレス
                </span>
              }
              span={2}
            >
              {user.email}
            </Descriptions.Item>

            <Descriptions.Item 
              label={
                <span>
                  <SafetyOutlined style={{ marginRight: 8 }} />
                  ロール
                </span>
              }
            >
              {user.role ? (
                <span style={{ 
                  padding: '2px 8px', 
                  borderRadius: '4px',
                  backgroundColor: user.role === 'admin' ? '#52c41a' : '#1890ff',
                  color: 'white',
                  fontSize: '12px',
                  fontWeight: 'bold'
                }}>
                  {user.role.toUpperCase()}
                </span>
              ) : (
                '(未設定)'
              )}
            </Descriptions.Item>
          </Descriptions>
        </Card>

        {/* 将来的な拡張用のプレースホルダー */}
        <Card title="アカウント設定" bordered={false}>
          <Alert
            message="準備中"
            description="パスワード変更、通知設定などの機能は今後追加予定です。"
            type="info"
            showIcon
          />
        </Card>
      </Space>
    </div>
  );
};

export default SettingsPage;
