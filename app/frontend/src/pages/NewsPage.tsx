import React from 'react';
import { Typography } from 'antd';

const { Title, Paragraph } = Typography;

const NewsPage: React.FC = () => (
  <div style={{ padding: 32 }}>
    <Title level={2}>お知らせ</Title>
    <Paragraph>現在表示できるお知らせはありません。</Paragraph>
  </div>
);

export default NewsPage;