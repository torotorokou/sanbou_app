/**
 * リファクタリング後のPortalCardコンポーネント
 * 小さなコンポーネントとカスタムフックに分割して保守性を向上
 */
import React from "react";
import { Card, Popover } from "antd";
import { useNavigate } from "react-router-dom";
import type { PortalCardProps } from "../model/types";
import { usePortalCardStyles } from "../model/usePortalCardStyles";
import { CardIcon } from "./CardIcon";
import { CardContent } from "./CardContent";
import { CardButton } from "./CardButton";

export const PortalCard: React.FC<PortalCardProps> = ({
  title,
  description,
  icon,
  link,
  detail,
  color,
  buttonWidth,
  cardScale,
  compactLayout,
  hideButton,
  smallButton,
  heightScale,
}) => {
  const navigate = useNavigate();

  // スタイル計算をカスタムフックに委譲
  const styles = usePortalCardStyles({
    color,
    buttonWidth,
    cardScale,
    compactLayout,
    hideButton,
    smallButton,
    heightScale,
  });

  const {
    accent,
    accentPlate,
    btnText,
    finalCardHeight,
    finalIconSize,
    finalIconFontSize,
    finalButtonHeight,
    finalButtonWidth,
    isButtonHidden,
    isSmallButton,
    titleFontSize,
    descriptionFontSize,
    buttonFontSize,
    scale,
    token,
  } = styles;

  const handleNavigate = () => navigate(link);
  const handleKeyDown: React.KeyboardEventHandler<HTMLDivElement> = (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      handleNavigate();
    }
  };

  return (
    <Popover
      content={detail ?? description}
      trigger={["hover"]}
      placement="top"
      overlayStyle={{ maxWidth: 320, whiteSpace: "normal" }}
    >
      <Card
        hoverable
        role="button"
        tabIndex={0}
        aria-label={`${title} カード`}
        onKeyDown={handleKeyDown}
        onClick={handleNavigate}
        style={{
          width: "100%",
          height: finalCardHeight,
          borderRadius: compactLayout ? 6 : 16,
          margin: compactLayout ? 0 : undefined,
          boxShadow: hideButton
            ? `inset 0 4px 0 0 ${accent}`
            : `inset 0 2px 0 0 ${accent}`,
          transition: "transform 200ms ease, box-shadow 200ms ease",
        }}
        styles={{
          body: {
            height: "100%",
            padding: compactLayout
              ? "1px 1px"
              : isButtonHidden
                ? "8px 12px"
                : "12px 12px",
            display: "flex",
            flexDirection:
              isButtonHidden || isSmallButton
                ? "row"
                : compactLayout
                  ? "row"
                  : "column",
            alignItems: "center",
            justifyContent: isSmallButton
              ? "space-between"
              : isButtonHidden
                ? "flex-start"
                : compactLayout
                  ? "space-between"
                  : "center",
            gap: compactLayout ? 6 * scale : 8 * scale,
            textAlign: isButtonHidden
              ? "left"
              : compactLayout
                ? "left"
                : "center",
          },
        }}
        onMouseEnter={(e) => {
          (e.currentTarget as HTMLDivElement).style.transform =
            "translateY(-2px)";
          (e.currentTarget as HTMLDivElement).style.zIndex = "2";
          (e.currentTarget as HTMLDivElement).style.boxShadow = hideButton
            ? `inset 0 4px 0 0 ${accent}, ${token.boxShadowSecondary}`
            : `inset 0 2px 0 0 ${accent}, ${token.boxShadowSecondary}`;
        }}
        onMouseLeave={(e) => {
          (e.currentTarget as HTMLDivElement).style.transform = "translateY(0)";
          (e.currentTarget as HTMLDivElement).style.zIndex = "0";
          (e.currentTarget as HTMLDivElement).style.boxShadow = hideButton
            ? `inset 0 4px 0 0 ${accent}`
            : `inset 0 2px 0 0 ${accent}`;
        }}
        onFocus={(e) => {
          (e.currentTarget as HTMLDivElement).style.zIndex = "2";
          (e.currentTarget as HTMLDivElement).style.boxShadow = hideButton
            ? `inset 0 4px 0 0 ${accent}, 0 0 0 3px ${token.colorPrimaryBorder}`
            : `inset 0 2px 0 0 ${accent}, 0 0 0 3px ${token.colorPrimaryBorder}`;
        }}
        onBlur={(e) => {
          (e.currentTarget as HTMLDivElement).style.zIndex = "0";
          (e.currentTarget as HTMLDivElement).style.boxShadow = hideButton
            ? `inset 0 4px 0 0 ${accent}`
            : `inset 0 2px 0 0 ${accent}`;
        }}
      >
        {/* アイコン */}
        <CardIcon
          icon={icon}
          size={finalIconSize}
          fontSize={finalIconFontSize}
          background={accentPlate}
          color={accent}
          isCompact={!!compactLayout}
          marginRight={compactLayout || isButtonHidden ? 12 : 0}
        />

        {/* コンテンツ（タイトル・説明） */}
        <CardContent
          title={title}
          description={description}
          titleFontSize={titleFontSize}
          descriptionFontSize={descriptionFontSize}
          isButtonHidden={isButtonHidden}
          isSmallButton={isSmallButton}
          compactLayout={!!compactLayout}
        />

        {/* ボタン */}
        {!isButtonHidden && (
          <CardButton
            title={title}
            onClick={(e) => {
              e.stopPropagation();
              handleNavigate();
            }}
            width={finalButtonWidth}
            height={finalButtonHeight}
            fontSize={buttonFontSize}
            backgroundColor={accent}
            textColor={btnText}
            backgroundImage={accentPlate}
            isSmallButton={isSmallButton}
            buttonWidth={buttonWidth}
          />
        )}
      </Card>
    </Popover>
  );
};
