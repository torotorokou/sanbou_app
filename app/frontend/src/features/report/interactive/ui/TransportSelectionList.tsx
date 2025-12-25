// UI component: Transport vendor selection card
import React from "react";
import { Card, Select } from "antd";
import type { InteractiveItem } from "@features/report/shared/types/interactive.types";

interface SelectionState {
  index: number;
  label: string;
}

export interface TransportSelectionCardProps {
  item: InteractiveItem;
  index: number;
  selection: SelectionState | undefined;
  onChange: (id: string, selection: SelectionState) => void;
}

/**
 * 処分業者ごとの運搬業者選択カード（1行分）
 */
export const TransportSelectionCard: React.FC<TransportSelectionCardProps> = ({
  item,
  index,
  selection,
  onChange,
}) => {
  const bgColor = index % 2 === 0 ? "#f5fbff" : "#fffaf0";
  const borderColor = index % 2 === 0 ? "#e6f7ff" : "#fff2cc";

  return (
    <Card
      size="small"
      style={{
        marginBottom: 4,
        padding: 0,
        background: bgColor,
        border: `1px solid ${borderColor}`,
        borderRadius: 8,
        boxShadow: "0 1px 0 rgba(0,0,0,0.02)",
        maxWidth: 820,
        marginInline: "auto",
      }}
      bodyStyle={{ padding: "4px 8px" }}
    >
      <div style={{ display: "flex", justifyContent: "center" }}>
        <div
          style={{
            display: "flex",
            gap: 12,
            alignItems: "flex-start",
            maxWidth: 760,
            width: "100%",
          }}
        >
          {/* 行番号 */}
          <div
            style={{
              minWidth: 44,
              textAlign: "center",
              fontSize: 13,
              fontWeight: 600,
              color: "#1890ff",
              paddingTop: 4,
            }}
          >
            {index + 1}
          </div>

          {/* 処分業者情報 */}
          <div
            style={{
              flex: "0 0 55%",
              lineHeight: 1.1,
              marginLeft: 8,
            }}
          >
            <div style={{ fontSize: 14 }}>
              <strong>処分業者：</strong> {item.processor_name}
            </div>
            <div style={{ fontSize: 14, marginTop: 2 }}>
              <strong>商品名：</strong> {item.product_name}
            </div>
            <div style={{ fontSize: 14, color: "#444", marginTop: 2 }}>
              <strong>備考：</strong> {item.note ?? "（なし）"}
            </div>
          </div>

          {/* 運搬業者選択 */}
          <div style={{ flex: "0 0 160px" }}>
            <div style={{ marginBottom: 2, fontSize: 14 }}>
              <strong>運搬業者：</strong> 選択
            </div>
            <Select
              style={{ width: "100%" }}
              dropdownMatchSelectWidth={false}
              placeholder="選択してください"
              value={selection?.index}
              onChange={(selected) => {
                const idxNum =
                  typeof selected === "number" ? selected : Number(selected);
                const clamped = Number.isFinite(idxNum)
                  ? Math.max(
                      0,
                      Math.min(idxNum, item.transport_options.length - 1),
                    )
                  : 0;
                const label = item.transport_options[clamped]?.name ?? "";
                onChange(item.id, { index: clamped, label });
              }}
              options={item.transport_options.map((v, optionIndex) => ({
                value: optionIndex,
                label: v.name,
              }))}
            />
          </div>
        </div>
      </div>
    </Card>
  );
};

export interface TransportSelectionListProps {
  items: InteractiveItem[];
  selections: Record<string, SelectionState>;
  onChange: (id: string, selection: SelectionState) => void;
}

/**
 * 運搬業者選択カードのリスト
 */
export const TransportSelectionList: React.FC<TransportSelectionListProps> = ({
  items,
  selections,
  onChange,
}) => {
  return (
    <div>
      {items.map((item, idx) => (
        <TransportSelectionCard
          key={item.id}
          item={item}
          index={idx}
          selection={selections[item.id]}
          onChange={onChange}
        />
      ))}
    </div>
  );
};
