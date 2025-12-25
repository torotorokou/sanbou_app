/**
 * SectionBlock UI Component
 * セクション単位でマニュアルアイテムを表示（純粋UI）
 */
import React from "react";
import { Badge, Col, Row, Space, Typography } from "antd";
import type {
  ManualItem,
  ManualSection,
} from "../../domain/types/shogun.types";
import { ItemCard } from "./ItemCard";

const { Title } = Typography;

export interface SectionBlockProps {
  section: ManualSection;
  onOpen: (item: ManualItem) => void;
  sectionClassName?: string;
  headerClassName?: string;
  itemClassName?: string;
}

export const SectionBlock: React.FC<SectionBlockProps> = ({
  section,
  onOpen,
  sectionClassName,
  headerClassName,
  itemClassName,
}) => {
  return (
    <div id={section.id} className={sectionClassName}>
      <Space align="center" size="middle" className={headerClassName}>
        <Title level={3} style={{ margin: 0 }}>
          {section.icon} {section.title}
        </Title>
        <Badge count={section.items.length} />
      </Space>
      <Row gutter={[16, 16]}>
        {section.items.map((item: ManualItem) => (
          <Col xs={24} lg={12} xl={8} key={item.id}>
            <ItemCard item={item} onOpen={onOpen} className={itemClassName} />
          </Col>
        ))}
      </Row>
    </div>
  );
};
