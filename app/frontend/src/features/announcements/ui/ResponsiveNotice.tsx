// src/features/announcements/ui/ResponsiveNotice.tsx
// スマホで大きすぎる通知を「1行バナー＋詳細Drawer」に置換（React+TypeScript, AntD）

import React, { useState } from "react";
import { Alert, Button, Drawer, Space, Typography } from "antd";
import { InfoCircleOutlined } from "@ant-design/icons";
import { BP, tierOf, useResponsive } from "@/shared";

export interface ResponsiveNoticeProps {
  title: string;
  description?: string;
  detailContent?: React.ReactNode;
  onClose?: () => void;
  type?: "info" | "warning" | "success" | "error";
}

export const ResponsiveNotice: React.FC<ResponsiveNoticeProps> = ({
  title,
  description,
  detailContent,
  onClose,
  type = "warning",
}) => {
  const [open, setOpen] = useState(false);
  const { width } = useResponsive();
  const tier = tierOf(width);
  const isMobile = width <= BP.mobileMax;

  const messageStyle: React.CSSProperties = {
    display: "flex",
    alignItems: "center",
    gap: 8,
    fontSize: isMobile ? "14px" : "clamp(13px, 3.2vw, 16px)",
    lineHeight: 1.4,
    whiteSpace: isMobile ? "normal" : "nowrap",
    overflow: isMobile ? "visible" : "hidden",
    textOverflow: isMobile ? "clip" : "ellipsis",
    fontWeight: isMobile ? 600 : "normal",
  };

  const containerStyle: React.CSSProperties = {
    padding: isMobile ? "12px 12px" : "clamp(8px, 2.4vw, 16px)",
  };

  // Action button: remove the small arrow icon to avoid proximity to the close mark.
  // Make the whole button tappable (text area) to open the drawer. Use small size on mobile.
  // Combine '詳細' and a small '閉じる' text link in the Alert action area.
  const actionButton = (
    <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
      <Button
        type="link"
        size={isMobile ? "small" : "middle"}
        onClick={(e) => {
          e.stopPropagation();
          setOpen(true);
        }}
        style={{ paddingInline: isMobile ? 8 : 8 }}
        aria-label="詳細を開く"
      >
        詳細
      </Button>
      <Button
        type="link"
        size={isMobile ? "small" : "middle"}
        onClick={(e) => {
          e.stopPropagation();
          // Inform the parent to hide the banner if handler provided
          if (onClose) onClose();
        }}
        style={{ paddingInline: isMobile ? 8 : 8, color: "inherit" }}
        aria-label="通知を閉じる"
      >
        閉じる
      </Button>
    </div>
  );

  return (
    <>
      {/*
        We intentionally do not render the Alert's built-in close icon to avoid
        duplication with our drawer/close affordances on small screens.
        Accept the `closable` prop for API compatibility, but do not pass it
        through to the underlying AntD Alert. If the parent wants to hide the
        banner entirely, they can call onClose which we still invoke when
        appropriate (we don't show an internal close button here).
      */}
      <Alert
        type={type}
        banner
        showIcon
        // Force no close icon here; closing is handled by parent via onClose
        closable={false}
        // Keep onClose available for parent control, but it's not triggered by a local close button
        // Parent can hide the notice by calling the onClose they provided
        icon={<InfoCircleOutlined />}
        style={containerStyle}
        message={
          <Space size={8} style={{ width: "100%", overflow: "hidden" }}>
            <span style={messageStyle}>
              <strong style={{ marginRight: 6 }}>{title}</strong>
              {description ? (
                <span style={{ opacity: 0.85 }}>{description}</span>
              ) : null}
            </span>
          </Space>
        }
        action={actionButton}
      />

      <Drawer
        open={open}
        onClose={() => setOpen(false)}
        title={title}
        placement="bottom"
        height={tier === "desktop" ? 360 : 320}
      >
        {detailContent ? (
          detailContent
        ) : description ? (
          <Typography.Paragraph>{description}</Typography.Paragraph>
        ) : null}
      </Drawer>
    </>
  );
};
