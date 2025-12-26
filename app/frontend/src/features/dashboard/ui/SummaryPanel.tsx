import { bp } from "@/shared";
import React from "react";
import { Card, Row, Col } from "antd";
import { CarOutlined, InboxOutlined } from "@ant-design/icons";
import { AnimatedStatistic, DiffIndicator, TrendChart } from "@shared/ui";

const SummaryPanel: React.FC = () => {
  const driveData = [
    {
      title: "月間搬入台数",
      value: 1381,
      suffix: "台",
      prefix: <CarOutlined />,
      diff: +52,
      trend: [bp.xl, 1240, 1260, 1290, 1300, 1340, 1381],
      minY: bp.xl,
      maxY: 1450,
    },
    {
      title: "終了台数（当日）",
      value: 120,
      suffix: "台",
      prefix: <CarOutlined />,
      diff: -7,
      trend: [122, 128, 125, 130, 124, 127, 120],
      minY: 100,
      maxY: 140,
    },
  ];

  const weightData = [
    {
      title: "月間搬入量",
      value: 860330,
      suffix: "kg",
      prefix: <InboxOutlined />,
      diff: +24500,
      trend: [790000, 805000, 820000, 830000, 845000, 860000, 860330],
    },
    {
      title: "当日搬入量",
      value: 102600,
      suffix: "kg",
      prefix: <InboxOutlined />,
      diff: +3200,
      trend: [98000, 99000, 99500, 100500, 78000, 98140, 102600],
    },
    {
      title: "当日搬出量",
      value: 127570,
      suffix: "kg",
      prefix: <InboxOutlined />,
      diff: -8100,
      trend: [130000, 129000, 128000, 128500, 127800, 127000, 127570],
    },
  ];

  return (
    <Card
      title={
        <span style={{ fontWeight: "bold", fontSize: 16 }}>
          🚛 月間搬入サマリー
        </span>
      }
      className="dashboard-card"
      styles={{ body: { padding: 12 } }}
    >
      <Row gutter={16}>
        <Col span={12}>
          <h4 style={{ marginBottom: 8, fontSize: 14 }}>🚚 搬入台数</h4>
          {driveData.map((item, index) => (
            <div
              key={index}
              style={{
                display: "flex",
                alignItems: "center",
                marginBottom: 8, // ← 間隔を詰める
                gap: 8, // ← gapも小さく
              }}
            >
              <div className="fluid-child" style={{ minWidth: 0 }}>
                {" "}
                {/* ← 幅も小さく */}
                <AnimatedStatistic
                  title={item.title}
                  value={item.value}
                  suffix={item.suffix}
                  prefix={item.prefix}
                />
                <div style={{ marginTop: 2 }}>
                  <DiffIndicator diff={item.diff} unit={item.suffix} />
                </div>
              </div>
              <div style={{ flex: 1 }}>
                <TrendChart
                  data={item.trend}
                  height={60} // ← グラフも小型化
                  minY={item.minY}
                  maxY={item.maxY}
                />
              </div>
            </div>
          ))}
        </Col>

        <Col span={12}>
          <h4 style={{ marginBottom: 8, fontSize: 14 }}>⚖️ 搬入・搬出量</h4>
          {weightData.map((item, index) => (
            <div
              key={index}
              style={{
                display: "flex",
                alignItems: "center",
                marginBottom: 8,
                gap: 8,
              }}
            >
              <div className="fluid-child" style={{ minWidth: 0 }}>
                <AnimatedStatistic
                  title={item.title}
                  value={item.value}
                  suffix={item.suffix}
                  prefix={item.prefix}
                />
                <div style={{ marginTop: 2 }}>
                  <DiffIndicator diff={item.diff} unit={item.suffix} />
                </div>
              </div>
              <div style={{ flex: 1 }}>
                <TrendChart data={item.trend} height={60} />
              </div>
            </div>
          ))}
        </Col>
      </Row>
    </Card>
  );
};

export default SummaryPanel;
