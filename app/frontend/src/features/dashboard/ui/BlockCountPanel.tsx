import React from "react";
import { Card, Row, Col } from "antd";
import { StatisticCard } from "@shared/ui";

const BlockCountPanel: React.FC = () => {
  const blockData = [
    { title: "廃プラ", value: 48, diff: 5 },
    { title: "焼却", value: 32, diff: -3 },
    { title: "破砕", value: 27, diff: 0 },
    { title: "安定", value: 19, diff: 2 },
    { title: "B", value: 12, diff: -1 },
  ];

  return (
    <Card title="🧱 ブロック数" className="dashboard-card">
      <Row gutter={0} justify="space-between">
        {blockData.map((item, index) => (
          <Col key={index} span={Math.floor(24 / blockData.length)}>
            <StatisticCard
              title={item.title}
              value={item.value}
              diff={item.diff}
              suffix="個"
              // prefix={<AppstoreOutlined />}
            />
          </Col>
        ))}
      </Row>
    </Card>
  );
};

export default BlockCountPanel;
