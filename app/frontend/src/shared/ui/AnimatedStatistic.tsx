// components/AnimatedStatistic.tsx
import React from "react";
import { Statistic } from "antd";
import CountUp from "react-countup";

interface AnimatedStatisticProps {
  title: React.ReactNode;
  value: number;
  suffix?: string;
  prefix?: React.ReactNode;
  color?: string;
}

const AnimatedStatistic: React.FC<AnimatedStatisticProps> = ({
  title,
  value,
  suffix,
  prefix,
  color = "black",
}) => {
  return (
    <Statistic
      title={title}
      prefix={prefix}
      suffix={suffix}
      value={value}
      valueRender={() => <CountUp end={value} duration={1.2} separator="," />}
      valueStyle={{ fontSize: "1.5rem", color }}
    />
  );
};

export default AnimatedStatistic;
