/**
 * アップロードカレンダー凡例
 * CSV種別の色とラベルを表示
 */

import React from "react";
import { Space, Typography } from "antd";
import { getMasterByDatasetKey } from "../model/types";

const { Text } = Typography;

interface UploadCalendarLegendProps {
  datasetKey?: string; // 選択中のデータセットキー
}

export const UploadCalendarLegend: React.FC<UploadCalendarLegendProps> = ({
  datasetKey = "shogun_flash",
}) => {
  // 選択中のデータセットに応じたマスタのみを取得
  const filteredMaster = getMasterByDatasetKey(datasetKey);

  // カテゴリごとにグループ化
  const categories = Array.from(new Set(filteredMaster.map((m) => m.category)));

  return (
    <div style={{ marginTop: 12, padding: "8px 0" }}>
      <Text
        type="secondary"
        style={{ fontSize: 13, marginBottom: 6, display: "block" }}
      >
        凡例
      </Text>
      <Space direction="vertical" size={4}>
        {categories.map((category) => {
          const kinds = filteredMaster.filter((m) => m.category === category);
          return (
            <div key={category}>
              <Text strong style={{ fontSize: 13 }}>
                {category}
              </Text>
              <Space size={8} wrap style={{ marginLeft: 8 }}>
                {kinds.map((master) => (
                  <Space key={master.kind} size={8}>
                    <span
                      style={{
                        display: "inline-block",
                        width: 14,
                        height: 14,
                        borderRadius: "50%",
                        backgroundColor: master.color,
                      }}
                    />
                    <Text style={{ fontSize: 13 }}>{master.label}</Text>
                  </Space>
                ))}
              </Space>
            </div>
          );
        })}
      </Space>
    </div>
  );
};
