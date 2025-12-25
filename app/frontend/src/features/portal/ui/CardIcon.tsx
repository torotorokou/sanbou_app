/**
 * PortalCardのアイコン部分のコンポーネント
 */
import React from "react";

interface CardIconProps {
  icon: React.ReactNode;
  size: number;
  fontSize: number;
  background: string;
  color: string;
  isCompact: boolean;
  marginRight?: number;
}

export const CardIcon: React.FC<CardIconProps> = ({
  icon,
  size,
  fontSize,
  background,
  color,
  isCompact,
  marginRight = 0,
}) => {
  return (
    <div
      aria-hidden
      style={{
        width: size,
        height: size,
        borderRadius: isCompact ? 8 : "50%",
        background,
        color,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontSize: `${fontSize}px`,
        lineHeight: 1,
        flex: "0 0 auto",
        marginRight: marginRight || 0,
      }}
    >
      {icon}
    </div>
  );
};
