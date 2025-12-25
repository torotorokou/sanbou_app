/**
 * PortalCardのコンテンツ部分（タイトル・説明）のコンポーネント
 */
import React from "react";
import { Typography, theme } from "antd";

const { Title, Paragraph } = Typography;

interface CardContentProps {
  title: string;
  description: string;
  titleFontSize: string;
  descriptionFontSize: string;
  isButtonHidden: boolean;
  isSmallButton: boolean;
  compactLayout: boolean;
}

export const CardContent: React.FC<CardContentProps> = ({
  title,
  description,
  titleFontSize,
  descriptionFontSize,
  isButtonHidden,
  isSmallButton,
  compactLayout,
}) => {
  const { token } = theme.useToken();

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems:
          isButtonHidden || isSmallButton
            ? "flex-start"
            : compactLayout
              ? "flex-start"
              : "center",
        flex:
          isButtonHidden || isSmallButton
            ? "1 1 auto"
            : isButtonHidden
              ? 1.4
              : 1,
      }}
    >
      <div style={{ maxWidth: isSmallButton ? 180 : 260 }}>
        <Title
          level={4}
          style={{
            margin: 0,
            lineHeight: 1.2,
            textAlign: isButtonHidden ? "left" : undefined,
            fontSize: titleFontSize,
            fontWeight: isButtonHidden || isSmallButton ? 600 : undefined,
          }}
        >
          {title}
        </Title>
      </div>
      {/* sm未満では説明を非表示（タイトルを大きめに表示） */}
      {!isButtonHidden && !isSmallButton && (
        <Paragraph
          style={{
            margin: 0,
            maxWidth: isButtonHidden ? "100%" : 260,
            display: "-webkit-box",
            WebkitLineClamp: compactLayout ? 1 : 2,
            WebkitBoxOrient: "vertical",
            overflow: "hidden",
            minHeight: compactLayout ? "1.4em" : "2.8em",
            color: token.colorTextSecondary,
            textAlign: isButtonHidden ? "left" : undefined,
            fontSize: descriptionFontSize,
          }}
          title={description}
        >
          {description}
        </Paragraph>
      )}
    </div>
  );
};
