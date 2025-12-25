/**
 * detail-chart/ui/DailySeriesChart.tsx
 * 日次推移折れ線グラフコンポーネント
 */

import React from "react";
import { Button, Space, Empty } from "antd";
import { ReloadOutlined } from "@ant-design/icons";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip as RTooltip,
} from "recharts";
import type {
  DailyPoint,
  YYYYMM,
  CategoryKind,
} from "../../shared/model/types";
import {
  fmtCurrency,
  fmtNumber,
  fmtUnitPrice,
} from "../../shared/model/metrics";

export interface DailySeriesChartProps {
  series?: DailyPoint[];
  repName: string;
  month?: YYYYMM;
  monthRange?: { from: YYYYMM; to: YYYYMM };
  onLoad: () => void;
  categoryKind: CategoryKind;
}

/**
 * 日次推移チャート
 */
export const DailySeriesChart: React.FC<DailySeriesChartProps> = ({
  series,
  repName,
  month,
  monthRange,
  onLoad,
  categoryKind,
}) => {
  const amountLabel = categoryKind === "waste" ? "売上" : "仕入";
  const periodLabel = month
    ? `${month} 日次推移`
    : `${monthRange!.from}〜${monthRange!.to} 日次推移`;

  return (
    <div>
      <Space
        align="baseline"
        style={{ justifyContent: "space-between", width: "100%" }}
      >
        <div className="card-subtitle">
          {periodLabel}（営業：{repName}）
        </div>
        {!series && (
          <Button size="small" onClick={onLoad} icon={<ReloadOutlined />}>
            日次を取得
          </Button>
        )}
      </Space>
      <div style={{ width: "100%", height: 320 }}>
        <ResponsiveContainer>
          {series && series.length > 0 ? (
            <LineChart
              data={series}
              margin={{ top: 8, right: 8, left: 8, bottom: 24 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <RTooltip
                formatter={(value: number, name: string) => {
                  if (name === amountLabel) return fmtCurrency(value);
                  if (name === "数量") return `${fmtNumber(value)} kg`;
                  if (name === "件数") return `${fmtNumber(value)} 件`;
                  if (name === "単価") return fmtUnitPrice(value);
                  return value;
                }}
              />
              <Line
                type="monotone"
                dataKey="amount"
                name={amountLabel}
                stroke="#237804"
              />
              <Line
                type="monotone"
                dataKey="qty"
                name="数量"
                stroke="#52c41a"
              />
              <Line
                type="monotone"
                dataKey="count"
                name="件数"
                stroke="#1890ff"
              />
            </LineChart>
          ) : (
            <Empty
              description="日次データがありません"
              style={{ paddingTop: 100 }}
            />
          )}
        </ResponsiveContainer>
      </div>
    </div>
  );
};
