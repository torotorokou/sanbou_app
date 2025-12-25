import React from "react";
import { Statistic } from "antd";
import CountUp from "react-countup";
import DiffIndicator from "./DiffIndicator";

type Props = {
  title: string | React.ReactNode;
  value: number;
  diff?: number;
  suffix?: string;
  prefix?: React.ReactNode;
  color?: string;
  titleHeight?: number;
};

const MetricCard: React.FC<Props> = ({
  title,
  value,
  diff,
  suffix = "",
  prefix,
  color = "#000",
  titleHeight = 40,
}) => {
  return (
    <div
      style={{
        height: 140,
        padding: 8,
        border: "1px solid #eee",
        borderRadius: 4,
        display: "flex",
        flexDirection: "column",
        alignItems: "center", // 横中央揃え
      }}
    >
      <Statistic
        title={
          <div
            style={{
              minHeight: titleHeight,
              textAlign: "center",
              whiteSpace: "pre-line",
            }}
          >
            {title}
          </div>
        }
        valueRender={() => (
          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: "1.5rem", color }}>
              <CountUp end={value} duration={1} separator="," />
              {suffix}
            </div>
            {diff !== undefined && (
              <div style={{ marginTop: 4 }}>
                <DiffIndicator diff={diff} unit={suffix} />
              </div>
            )}
          </div>
        )}
        prefix={prefix}
      />
    </div>
  );
};

export default MetricCard;
