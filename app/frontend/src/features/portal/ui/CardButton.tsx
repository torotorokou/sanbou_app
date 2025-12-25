/**
 * PortalCardのボタン部分のコンポーネント
 */
import React from "react";
import { Button } from "antd";
import { BUTTON_WIDTH, BUTTON_HEIGHT } from "../domain/constants";

interface CardButtonProps {
  title: string;
  onClick: (e: React.MouseEvent) => void;
  width: number;
  height: number;
  fontSize: string;
  backgroundColor: string;
  textColor: string;
  backgroundImage: string;
  isSmallButton: boolean;
  buttonWidth?: number;
}

export const CardButton: React.FC<CardButtonProps> = ({
  title,
  onClick,
  width,
  height,
  fontSize,
  backgroundColor,
  textColor,
  backgroundImage,
  isSmallButton,
  buttonWidth,
}) => {
  const finalWidth = isSmallButton
    ? Math.round((buttonWidth ?? BUTTON_WIDTH) * 0.5)
    : width;
  const finalHeight = isSmallButton ? Math.round(BUTTON_HEIGHT * 0.78) : height;

  return (
    <Button
      type="primary"
      size="middle"
      style={{
        width: finalWidth,
        minWidth: finalWidth,
        maxWidth: finalWidth,
        height: finalHeight,
        lineHeight: `${finalHeight}px`,
        fontSize,
        padding: 0,
        whiteSpace: "nowrap",
        flex: "0 0 auto",
        alignSelf: "center",
        backgroundColor,
        borderColor: "transparent",
        color: textColor,
        backgroundImage,
        backgroundRepeat: "no-repeat",
        backgroundSize: "cover",
        boxShadow: "none",
      }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLButtonElement).style.transform =
          "translateY(-1px)";
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLButtonElement).style.transform =
          "translateY(0)";
      }}
      onClick={onClick}
      aria-label={`${title} へ移動`}
    >
      開く
    </Button>
  );
};
