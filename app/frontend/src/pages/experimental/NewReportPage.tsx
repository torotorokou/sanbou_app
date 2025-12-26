/**
 * 新レポートページ (実験的機能)
 *
 * @description
 * この機能は VITE_FF_NEW_REPORT=true の環境でのみ利用可能です。
 * フラグが OFF の環境では、ルートが接続されないため URL 直打ちでも 404 になります。
 *
 * @example
 * // env ファイルで有効化
 * VITE_FF_NEW_REPORT=true
 *
 * // アクセス URL
 * /experimental/new-report
 */
import React from "react";
import { Typography, Card, Alert, Space, Tag } from "antd";
import { ExperimentOutlined } from "@ant-design/icons";
import { getAllFeatureFlags } from "@/shared";

const { Title, Paragraph, Text } = Typography;

export const NewReportPage: React.FC = () => {
  const flags = getAllFeatureFlags();

  return (
    <div style={{ padding: "24px", maxWidth: "800px", margin: "0 auto" }}>
      <Space direction="vertical" size="large" style={{ width: "100%" }}>
        <Alert
          type="info"
          showIcon
          icon={<ExperimentOutlined />}
          message="実験的機能"
          description="このページは Feature Flag によって制御されています。本番環境ではフラグが OFF のため、アクセスできません。"
        />

        <Card>
          <Title level={2}>
            <ExperimentOutlined style={{ marginRight: 8 }} />
            新レポート機能
          </Title>

          <Paragraph>
            これは <Tag color="blue">VITE_FF_NEW_REPORT</Tag>{" "}
            フラグによって制御される 実験的な機能のサンプルページです。
          </Paragraph>

          <Paragraph>
            <Text strong>このパターンのポイント:</Text>
          </Paragraph>

          <ul>
            <li>フラグ OFF の環境では、このルートは存在しない (404)</li>
            <li>URL 直打ちでもアクセス不可</li>
            <li>サイドバー/ナビにもリンクが表示されない</li>
            <li>dev/stg では ON、prod では OFF が推奨</li>
          </ul>
        </Card>

        <Card title="現在の Feature Flags 状態" size="small">
          <pre style={{ margin: 0, fontSize: 12 }}>
            {JSON.stringify(flags, null, 2)}
          </pre>
        </Card>
      </Space>
    </div>
  );
};
