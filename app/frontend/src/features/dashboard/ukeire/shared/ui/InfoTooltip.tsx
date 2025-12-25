import React from "react";
import { Tooltip } from "antd";
import { InfoCircleOutlined } from "@ant-design/icons";

export type InfoTooltipProps = {
  title?: React.ReactNode;
  placement?:
    | "top"
    | "left"
    | "right"
    | "bottom"
    | "topLeft"
    | "topRight"
    | "bottomLeft"
    | "bottomRight"
    | "leftTop"
    | "leftBottom"
    | "rightTop"
    | "rightBottom";
  className?: string;
};

const defaultTitle = (
  <div>
    <div>先日: 28日前（同曜日）</div>
    <div>前年: 365日前（前年同曜日）</div>
  </div>
);

export const InfoTooltip: React.FC<InfoTooltipProps> = ({
  title = defaultTitle,
  placement = "top",
  className,
}) => {
  return (
    <Tooltip
      title={title}
      placement={placement}
      classNames={{ root: className }}
    >
      <InfoCircleOutlined style={{ color: "#8c8c8c" }} />
    </Tooltip>
  );
};
