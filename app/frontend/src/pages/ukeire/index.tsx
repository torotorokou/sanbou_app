/**
 * 受入量ダッシュボードページ
 * MVVM構造に則ったコンポーネント統合
 */

import React from "react";
import { Col, Row, Space, Typography } from "antd";
import { useUkeireForecastVM } from "@/features/ukeireVolume/forecast/hooks/useUkeireForecastVM";
import { MockUkeireForecastRepository } from "@/features/ukeireVolume/forecast/repository/MockUkeireForecastRepository";
import { TargetCard } from "@/features/kpiTarget/ui/TargetCard";
import CalendarCardUkeire from "@/features/ukeireVolume/actuals/ui/CalendarCard.Ukeire";
import { CombinedDailyCard } from "@/features/ukeireVolume/history/ui/CombinedDailyCard";
import { ForecastCard } from "@/features/ukeireVolume/forecast/ui/ForecastCard";

const { Title } = Typography;

// 開発中はMockRepositoryを使用
const repository = new MockUkeireForecastRepository();

export function UkeirePage() {
  const vm = useUkeireForecastVM(repository);

  // CalendarCard用のyear/month
  const [year, month] = vm.month.split("-").map(Number);

  return (
    <Space direction="vertical" size="large" style={{ width: "100%" }}>
      <Title level={2}>受入量ダッシュボード</Title>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} md={8}>
          {vm.targetCardProps && <TargetCard {...vm.targetCardProps} />}
        </Col>
        <Col xs={24} sm={12} md={8}>
          <CalendarCardUkeire year={year} month={month} />
        </Col>
        <Col xs={24} md={8}>
          {vm.combinedDailyProps && <CombinedDailyCard {...vm.combinedDailyProps} />}
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col span={24}>
          {vm.forecastCardProps && <ForecastCard {...vm.forecastCardProps} />}
        </Col>
      </Row>
    </Space>
  );
}

export default UkeirePage;
