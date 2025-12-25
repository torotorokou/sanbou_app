/**
 * export-menu/ui/ExportMenu.tsx
 * CSV出力メニューコンポーネント
 */

import React from "react";
import { Space, Switch, Select } from "antd";
import type { MenuProps } from "antd";
import type { ExportOptions, Mode } from "../../shared/model/types";
import { axisLabel } from "../../shared/model/metrics";

export interface ExportMenuProps {
  exportOptions: ExportOptions;
  onExportOptionsChange: (
    options: ExportOptions | ((prev: ExportOptions) => ExportOptions),
  ) => void;
  axB: Mode;
  axC: Mode;
}

/**
 * CSV出力メニュー項目生成
 */
export const createExportMenu = (
  props: ExportMenuProps,
): MenuProps["items"] => {
  const { exportOptions, onExportOptionsChange, axB, axC } = props;

  return [
    { key: "title", label: <b>出力条件</b> },
    { type: "divider" as const },

    // 追加カラム：残りモード1
    {
      key: "addB",
      label: (
        <div onClick={(e) => e.stopPropagation()}>
          <Space>
            <Switch
              size="small"
              checked={exportOptions.addAxisB}
              onChange={(v) =>
                onExportOptionsChange((prev) => ({ ...prev, addAxisB: v }))
              }
            />
            <span>追加カラム：{axisLabel(axB)}</span>
          </Space>
        </div>
      ),
    },

    // 追加カラム：残りモード2
    {
      key: "addC",
      label: (
        <div onClick={(e) => e.stopPropagation()}>
          <Space>
            <Switch
              size="small"
              checked={exportOptions.addAxisC}
              onChange={(v) =>
                onExportOptionsChange((prev) => ({ ...prev, addAxisC: v }))
              }
            />
            <span>追加カラム：{axisLabel(axC)}</span>
          </Space>
        </div>
      ),
    },

    { type: "divider" as const },

    // 0実績除外
    {
      key: "opt-zero",
      label: (
        <Space onClick={(e) => e.stopPropagation()}>
          <Switch
            size="small"
            checked={exportOptions.excludeZero}
            onChange={(checked) =>
              onExportOptionsChange((prev) => ({
                ...prev,
                excludeZero: checked,
              }))
            }
          />
          <span>0実績を除外する（Excel負荷対策）</span>
        </Space>
      ),
    },

    // 分割出力
    {
      key: "opt-split",
      label: (
        <Space onClick={(e) => e.stopPropagation()}>
          <Select
            size="small"
            value={exportOptions.splitBy}
            onChange={(v: "none" | "rep") =>
              onExportOptionsChange((prev) => ({ ...prev, splitBy: v }))
            }
            options={[
              { label: "分割しない", value: "none" },
              { label: "営業ごとに分割", value: "rep" },
            ]}
            style={{ width: 180 }}
          />
          <span>（Excel負荷対策）</span>
        </Space>
      ),
    },
  ];
};
