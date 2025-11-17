/**
 * TargetCard Component
 * 目標達成状況を表示するカード
 */

import React from "react";
import { Card, Space, Typography, Tooltip, Statistic, Progress, Segmented } from "antd";
import "./TargetCard.overrides.css";
import dayjs from "dayjs";
import isoWeekPlugin from "dayjs/plugin/isoWeek";
import { InfoCircleOutlined } from "@ant-design/icons";
import { COLORS } from "@/features/dashboard/ukeire/domain/constants";
import { clamp } from "@/features/dashboard/ukeire/domain/valueObjects";

export type AchievementMode = "toDate" | "toEnd";

export type TargetCardRowData = {
  key: string;
  label: string;
  target: number | null;
  actual: number | null;
};

export type TargetCardProps = {
  rows: TargetCardRowData[];
  style?: React.CSSProperties;
  isMobile?: boolean; // Mobile モードでフォントサイズを動的に調整
  isoWeek?: number; // 将来的にはバックグラウンドから取得する想定。指定があればそれを優先して表示する
  achievementMode?: AchievementMode; // 達成率モード（親コンポーネントで管理）
  onModeChange?: (mode: AchievementMode) => void; // モード変更コールバック
};

export const TargetCard: React.FC<TargetCardProps> = ({ 
  rows, 
  style, 
  isMobile = false, 
  isoWeek,
  achievementMode = "toDate",
  onModeChange,
}) => {
  // isoWeek プラグインを拡張
  dayjs.extend(isoWeekPlugin);
  // Mobile モードでは clamp を使って動的にフォントサイズを調整
  const headerFontSize = isMobile ? "clamp(12px, 3.5vw, 16px)" : "16px";
  const labelFontSize = isMobile ? "clamp(10px, 2.5vw, 12px)" : "12px";
  const valueFontSize = isMobile ? "clamp(14px, 4vw, 18px)" : "18px";
  const pctFontSize = isMobile ? "clamp(10px, 2.5vw, 12px)" : "12px";
  
  // Mobile モードでは行の高さを詰める
  const minRowHeight = isMobile ? 32 : 44;
  const gridPadding = isMobile ? 6 : 8;
  const rowGap = isMobile ? 4 : 6;

  return (
    <Card
      variant="outlined"
      style={{ height: "100%", display: "flex", flexDirection: "column", ...style }}
      styles={{ body: { padding: 12, display: "flex", flexDirection: "column", gap: 8, flex: 1, minHeight: 0 } }}
    >
      {/* ヘッダー: タイトル・ツールチップ・モード切り替え */}
      <Space direction="vertical" size={8} style={{ width: "100%" }}>
        <Space align="baseline" style={{ justifyContent: "space-between", width: "100%" }}>
          <Space align="baseline">
            <Typography.Title level={5} style={{ margin: 0 }}>
              目標カード
            </Typography.Title>
            <Tooltip title="週目標は当月の営業日配分で按分。日目標は平日/土/日祝の重みで配分。">
              <InfoCircleOutlined style={{ color: "#8c8c8c" }} />
            </Tooltip>
          </Space>
          
          {/* 達成率モード切り替え（親のコールバックを呼び出す） - 右寄せ */}
            {onModeChange && (
              <Segmented
                className="customSegmented"
                value={achievementMode}
                onChange={(value) => onModeChange(value as AchievementMode)}
                options={[
                  { label: isMobile ? "累計" : "昨日まで", value: "toDate" },
                  { label: isMobile ? "期末" : "月末・週末", value: "toEnd" },
                ]}
                size={isMobile ? "small" : "middle"}
                style={{ width: isMobile ? "auto" : "auto" }}
              />
            )}
        </Space>
      </Space>

      <div
        style={{
          border: "1px solid #f0f0f0",
          borderRadius: 8,
          background: "#fff",
          padding: gridPadding,
          display: "grid",
          gridTemplateColumns: "auto auto auto 1fr",
          gridTemplateRows: `repeat(${1 + rows.length}, minmax(${minRowHeight}px, 1fr))`,
          columnGap: isMobile ? 8 : 12,
          rowGap: rowGap,
          alignItems: "center",
          boxSizing: "border-box",
          flex: 1,
          minHeight: 0,
          overflow: "hidden",
        }}
      >
        {/* ヘッダ行 */}
  <div style={{ color: "#8c8c8c", fontSize: headerFontSize }} />
  <div style={{ color: "#8c8c8c", fontSize: headerFontSize, fontWeight: 700, textAlign: "center", justifySelf: "center" }}>目標</div>
  <div style={{ color: "#8c8c8c", fontSize: headerFontSize, fontWeight: 700, textAlign: "center", justifySelf: "center" }}>実績</div>
  <div style={{ color: "#8c8c8c", fontSize: headerFontSize, fontWeight: 700, textAlign: "center", justifySelf: "center" }}>達成率</div>

        {/* データ行 */}
        {rows.map((r) => {
          // NULL値をチェックして達成率を計算
          const ratioRaw = (r.target !== null && r.actual !== null && r.target > 0) 
            ? r.actual / r.target 
            : 0;
          const pct = (r.target !== null && r.actual !== null && r.target > 0) 
            ? Math.round(ratioRaw * 100) 
            : 0;
          const barPct = clamp(pct, 0, 100);
          const pctColor = ratioRaw >= 1 ? COLORS.ok : ratioRaw >= 0.9 ? COLORS.warn : COLORS.danger;
          
          // NULL値の場合は達成率を非表示にするかどうか
          const hasValidData = r.target !== null && r.actual !== null;
          
          // determine iso week to show: prefer prop on the component; fallback to computing from today
          let isoWeekToShow: number | undefined = typeof isoWeek === "number" ? isoWeek : undefined;
          if (isoWeekToShow === undefined) {
            isoWeekToShow = dayjs().isoWeek();
          }

          return (
            <React.Fragment key={r.key}>
              <div style={{ color: "#595959", fontSize: labelFontSize, fontWeight: 800, lineHeight: 1 }}>
                {/* 今週のラベルにはW##を表示 */}
                {(() => {
                  const label = r.label ?? "";
                  const isThisWeekLabel = label.startsWith("今週");
                  if (isThisWeekLabel && typeof isoWeekToShow === "number") {
                    const w = String(isoWeekToShow).padStart(2, "0");
                    if (isMobile) {
                      // Mobile: 1行で表示（ラベルを短縮してW##を強調）
                      return (
                        <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                          <span>今週</span>
                          <span style={{ color: "#1890ff", fontWeight: 700, fontSize: "0.9em" }}>{`W${w}`}</span>
                        </div>
                      );
                    }
                    // Desktop: 2行で表示（ラベルとW##を分ける）
                    return (
                      <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
                        <span>{label.replace("今週", "今週")}</span>
                        <span style={{ color: "#1890ff", fontWeight: 700, fontSize: "0.85em" }}>{`W${w}`}</span>
                      </div>
                    );
                  }
                  return <>{label}</>;
                })()}
              </div>
              <div>
                {r.target !== null ? (
                  <Statistic
                    value={Math.round(r.target)}
                    suffix="t"
                    valueStyle={{ color: COLORS.primary, fontSize: valueFontSize, fontWeight: 800, lineHeight: 1 }}
                    style={{ lineHeight: 1 }}
                  />
                ) : (
                  <div style={{ color: "#8c8c8c", fontSize: valueFontSize, fontWeight: 800, lineHeight: 1, textAlign: "center" }}>
                    —
                  </div>
                )}
              </div>
              <div>
                {r.actual !== null ? (
                  <Statistic
                    value={Math.round(r.actual)}
                    suffix="t"
                    valueStyle={{ color: "#222", fontSize: valueFontSize, fontWeight: 800, lineHeight: 1 }}
                    style={{ lineHeight: 1 }}
                  />
                ) : (
                  <div style={{ color: "#8c8c8c", fontSize: valueFontSize, fontWeight: 800, lineHeight: 1, textAlign: "center" }}>
                    —
                  </div>
                )}
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 4, minHeight: 0, overflow: "hidden" }}>
                {hasValidData ? (
                  <>
                    <div style={{ display: "flex", justifyContent: "flex-end", alignItems: "baseline" }}>
                      <Statistic
                        value={pct}
                        suffix="%"
                        valueStyle={{ color: pctColor, fontSize: pctFontSize, fontWeight: 700, lineHeight: 1 }}
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
                  </>
                ) : (
                  <div style={{ color: "#8c8c8c", fontSize: pctFontSize, fontWeight: 700, lineHeight: 1, textAlign: "right" }}>
                    —
                  </div>
                )}
              </div>
            </React.Fragment>
          );
        })}
      </div>
    </Card>
  );
};
