/**
 * TargetCard Component
 * 目標達成状況を表示するカード
 */

import React from "react";
import { Card, Space, Typography, Tooltip, Statistic, Progress } from "antd";
import { InfoCircleOutlined } from "@ant-design/icons";
import { COLORS } from "../../model/constants";
import { clamp } from "../../model/valueObjects";

export type TargetCardRowData = {
  key: string;
  label: string;
  target: number;
  actual: number;
};

export type TargetCardProps = {
  rows: TargetCardRowData[];
  style?: React.CSSProperties;
};

export const TargetCard: React.FC<TargetCardProps> = ({ rows, style }) => {
  return (
    <Card
      bordered
      style={{ height: "100%", display: "flex", flexDirection: "column", ...style }}
      bodyStyle={{ padding: 12, display: "flex", flexDirection: "column", gap: 8, flex: 1, minHeight: 0 }}
    >
      <Space align="baseline" style={{ justifyContent: "space-between", width: "100%" }}>
        <Typography.Title level={5} style={{ margin: 0 }}>
          目標カード
        </Typography.Title>
        <Tooltip title="週目標は当月の営業日配分で按分。日目標は平日/土/日祝の重みで配分。">
          <InfoCircleOutlined style={{ color: "#8c8c8c" }} />
        </Tooltip>
      </Space>

      <div
        style={{
          border: "1px solid #f0f0f0",
          borderRadius: 8,
          background: "#fff",
          padding: 8,
          display: "grid",
          gridTemplateColumns: "auto auto auto 1fr",
          gridTemplateRows: `repeat(${1 + rows.length}, minmax(44px, 1fr))`,
          columnGap: 12,
          rowGap: 6,
          alignItems: "center",
          boxSizing: "border-box",
          flex: 1,
          minHeight: 0,
          overflow: "hidden",
        }}
      >
        {/* ヘッダ行 */}
        <div style={{ color: "#8c8c8c", fontSize: 14 }} />
        <div style={{ color: "#8c8c8c", fontSize: 16, fontWeight: 700 }}>目標</div>
        <div style={{ color: "#8c8c8c", fontSize: 16, fontWeight: 700 }}>実績</div>
        <div style={{ color: "#8c8c8c", fontSize: 16, fontWeight: 700 }}>達成率</div>

        {/* データ行 */}
        {rows.map((r) => {
          const ratioRaw = r.target ? r.actual / r.target : 0;
          const pct = r.target ? Math.round(ratioRaw * 100) : 0;
          const barPct = clamp(pct, 0, 100);
          const pctColor = ratioRaw >= 1 ? COLORS.ok : ratioRaw >= 0.9 ? COLORS.warn : COLORS.danger;

          return (
            <React.Fragment key={r.key}>
              <div style={{ color: "#595959", fontSize: 12, fontWeight: 800, lineHeight: 1 }}>
                {r.label}
              </div>
              <div>
                <Statistic
                  value={typeof r.target === "number" ? r.target : 0}
                  suffix="t"
                  valueStyle={{ color: COLORS.primary, fontSize: 18, fontWeight: 800, lineHeight: 1 }}
                  style={{ lineHeight: 1 }}
                />
              </div>
              <div>
                <Statistic
                  value={typeof r.actual === "number" ? r.actual : 0}
                  suffix="t"
                  valueStyle={{ color: "#222", fontSize: 18, fontWeight: 800, lineHeight: 1 }}
                  style={{ lineHeight: 1 }}
                />
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 4, minHeight: 0, overflow: "hidden" }}>
                <div style={{ display: "flex", justifyContent: "flex-end", alignItems: "baseline" }}>
                  <Statistic
                    value={pct}
                    suffix="%"
                    valueStyle={{ color: pctColor, fontSize: 12, fontWeight: 700, lineHeight: 1 }}
                    style={{ lineHeight: 1 }}
                  />
                </div>
                <Progress
                  percent={barPct}
                  showInfo={false}
                  strokeColor={pctColor}
                  strokeWidth={8}
                  style={{ margin: 0 }}
                />
              </div>
            </React.Fragment>
          );
        })}
      </div>
    </Card>
  );
};
