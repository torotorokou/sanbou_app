/**
 * Environment Variables Test Page
 * 環境変数が正しく読み込まれているかテストするページ
 */

import React from 'react';
import { Card, Typography, Descriptions } from 'antd';

const { Title, Text } = Typography;

export default function EnvTestPage() {
  const envVars = {
    VITE_API_BASE_URL: import.meta.env.VITE_API_BASE_URL,
    MODE: import.meta.env.MODE,
    DEV: import.meta.env.DEV,
    PROD: import.meta.env.PROD,
    BASE_URL: import.meta.env.BASE_URL,
  };

  return (
    <div style={{ padding: 24 }}>
      <Card>
        <Title level={2}>環境変数テスト</Title>
        <Text type="secondary">import.meta.env で参照可能な環境変数の一覧</Text>

        <Descriptions bordered column={1} style={{ marginTop: 24 }}>
          {Object.entries(envVars).map(([key, value]) => (
            <Descriptions.Item key={key} label={key}>
              <Text code>{String(value)}</Text>
            </Descriptions.Item>
          ))}
        </Descriptions>

        <Title level={4} style={{ marginTop: 32 }}>
          すべての VITE_ 環境変数
        </Title>
        <pre
          style={{
            background: '#f5f5f5',
            padding: 16,
            borderRadius: 4,
            overflow: 'auto',
          }}
        >
          {JSON.stringify(
            Object.entries(import.meta.env)
              .filter(([key]) => key.startsWith('VITE_'))
              .reduce((acc, [key, value]) => ({ ...acc, [key]: value }), {}),
            null,
            2
          )}
        </pre>
      </Card>
    </div>
  );
}
