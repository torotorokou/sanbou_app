/**
 * ItemCard UI Component
 * 将軍マニュアルアイテムのカード表示（純粋UI）
 */
import React, { memo } from "react";
import { Card, Space, Tag, Typography } from "antd";
import { useResponsive } from "@/shared";
import type { ManualItem } from "../../domain/types/shogun.types";

const { Paragraph, Text } = Typography;

export interface ItemCardProps {
  item: ManualItem;
  onOpen: (item: ManualItem) => void;
  className?: string;
}

export const ItemCard: React.FC<ItemCardProps> = memo(
  ({ item, onOpen, className }) => {
    const { isMobile } = useResponsive();

    return (
      <Card
        size="small"
        className={className}
        hoverable
        onClick={() => onOpen(item)}
        title={<Text strong>{item.title}</Text>}
        style={{ height: "100%", display: "flex", flexDirection: "column" }}
        bodyStyle={{ flex: 1, display: "flex", flexDirection: "column" }}
        cover={
          item.thumbnailUrl || item.flowUrl ? (
            <div
              style={{
                width: "100%",
                aspectRatio: "16 / 9",
                overflow: "hidden",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                backgroundColor: "#f5f5f5",
                borderRadius: "8px 8px 0 0",
              }}
            >
              <img
                alt={item.title}
                src={item.thumbnailUrl || item.flowUrl}
                style={{
                  width: "100%",
                  height: "100%",
                  objectFit: "contain",
                  display: "block",
                }}
                onError={(e) => {
                  // 画像読み込みエラー時は非表示
                  (e.target as HTMLImageElement).style.display = "none";
                }}
              />
            </div>
          ) : undefined
        }
      >
        <Space direction="vertical" size={8} style={{ width: "100%", flex: 1 }}>
          {/* モバイルでは説明を非表示 */}
          {!isMobile && (
            <Paragraph
              type="secondary"
              ellipsis={{ rows: 5 }}
              style={{ marginBottom: 8, minHeight: "7.5em" }}
            >
              {item.description ?? "説明は未設定です。"}
            </Paragraph>
          )}
          <Space
            size={[4, 4]}
            wrap
            style={{ marginTop: isMobile ? 0 : "auto" }}
          >
            {(item.tags ?? []).map((t: string) => (
              <Tag key={t}>{t}</Tag>
            ))}
          </Space>
        </Space>
      </Card>
    );
  },
);

ItemCard.displayName = "ItemCard";
