/**
 * SingleLineLegend Component
 * 1行表示固定の凡例コンポーネント（実績項目は非表示）
 */

import React from "react";
import { FONT } from "../../domain/constants";

// Recharts Legend types
interface LegendPayloadItem {
  dataKey?: string;
  value?: string;
  payloadKey?: string;
  color?: string;
  payload?: {
    color?: string;
    [key: string]: unknown;
  };
  [key: string]: unknown;
}

interface LegendPropsLike {
  payload?: readonly LegendPayloadItem[];
  extraStatic?: { label: string; color: string }[];
  [key: string]: unknown;
}

export const SingleLineLegend: React.FC<LegendPropsLike> = (props) => {
  const payload = props.payload;
  const extraStatic = props.extraStatic ?? [];
  if ((!payload || !Array.isArray(payload)) && extraStatic.length === 0) return null;

  const map: Record<string, string> = {
    prevMonth: "先月",
    prevYear: "前年",
    prevMonthCumulative: "先月累積",
    prevYearCumulative: "前年累積",
    actual: "実績",
    actualCumulative: "実績累積",
    cumActual: "実績累積",
    cumDaily: "バック予測累積",
    dailyForward: "フロント予測",
    daily: "バック予測",
  };

  const normalizeLabel = (p: LegendPayloadItem) => {
    const rawKey = p.dataKey ?? p.value ?? p.payloadKey ?? "";
    const key = String(rawKey);
    if (
      key === "先月" ||
      key === "前年" ||
      key === "実績" ||
      key === "先月累積" ||
      key === "前年累積" ||
      key === "実績累積"
    )
      return key;
    return map[key] ?? key;
  };

  const items = (payload ?? []).filter((p) => {
    const raw = p.dataKey ?? p.value ?? "";
    const name = String(raw);
    if (
      name === "actual" ||
      name === "実績" ||
      name === "actualCumulative" ||
      name === "実績累積"
    )
      return false;
    return true;
  });

  if (items.length === 0 && extraStatic.length === 0) return null;

  return (
    <div
      style={{
        display: "flex",
        gap: 12,
        alignItems: "center",
        justifyContent: "center",
        whiteSpace: "nowrap",
        overflowX: "auto",
        padding: "4px 0",
      }}
    >
      {items.map((p, i) => {
        const label = normalizeLabel(p);
        if (label === "実績") return null;
        const color = p.color ?? p.payload?.color ?? "#ccc";
        return (
          <div key={i} style={{ display: "flex", gap: 6, alignItems: "center" }}>
            <div
              style={{
                width: 14,
                height: 14,
                borderRadius: 3,
                background: String(color),
              }}
            />
            <div style={{ color: "#595959", fontSize: FONT.size }}>{label}</div>
          </div>
        );
      })}
      {extraStatic.map((ex, i) => (
        <div key={`ex-${i}`} style={{ display: "flex", gap: 6, alignItems: "center" }}>
          <div style={{ width: 14, height: 14, borderRadius: 3, background: ex.color }} />
          <div style={{ color: "#595959", fontSize: FONT.size }}>{ex.label}</div>
        </div>
      ))}
    </div>
  );
};
/* eslint-enable @typescript-eslint/no-explicit-any */
