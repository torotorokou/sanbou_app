import React from "react";
import { Typography } from "antd";

const TestPage: React.FC = () => {
  return (
    <div style={{ padding: "24px", textAlign: "center" }}>
      <Typography.Title level={1}>
        🎉 アプリケーションが正常に動作しています！
      </Typography.Title>
      <Typography.Paragraph>
        このページが表示されている場合、基本的なReactアプリケーションは動作しています。
      </Typography.Paragraph>
      <Typography.Text type="secondary">
        レスポンシブデザインのテスト用ページです。
      </Typography.Text>
    </div>
  );
};

export default TestPage;
