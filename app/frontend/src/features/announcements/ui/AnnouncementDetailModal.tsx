/**
 * AnnouncementDetailModal - お知らせ詳細モーダルUI
 *
 * お知らせの詳細を表示するモーダル。
 * 状態レス：propsのみで動作。
 */

import React from "react";
import { Modal, Tag, Typography, Divider } from "antd";
import type { Announcement } from "../domain/announcement";

const { Title, Text } = Typography;

interface AnnouncementDetailModalProps {
  /** 表示するお知らせ（nullの場合は表示しない） */
  announcement: Announcement | null;
  /** モーダルが開いているかどうか */
  open: boolean;
  /** 閉じるコールバック */
  onClose: () => void;
}

/**
 * 重要度に応じたタグ色を返す
 */
function getSeverityTagColor(severity: Announcement["severity"]): string {
  switch (severity) {
    case "critical":
      return "red";
    case "warn":
      return "orange";
    case "info":
    default:
      return "blue";
  }
}

/**
 * 重要度に応じたラベルを返す
 */
function getSeverityLabel(severity: Announcement["severity"]): string {
  switch (severity) {
    case "critical":
      return "重要";
    case "warn":
      return "注意";
    case "info":
    default:
      return "情報";
  }
}

/**
 * 日付をフォーマット
 */
function formatDate(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleDateString("ja-JP", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
}

/**
 * 簡易的なMarkdown→プレーンテキスト変換
 * 本格的なレンダリングが必要な場合は react-markdown 等を使用
 */
function renderMarkdownSimple(md: string): React.ReactNode {
  // 見出し、リスト、強調を簡易的に処理
  const lines = md.split("\n");
  return lines.map((line, index) => {
    // 見出し
    if (line.startsWith("## ")) {
      return (
        <Title level={4} key={index} style={{ marginTop: 16, marginBottom: 8 }}>
          {line.replace("## ", "")}
        </Title>
      );
    }
    if (line.startsWith("### ")) {
      return (
        <Title level={5} key={index} style={{ marginTop: 12, marginBottom: 8 }}>
          {line.replace("### ", "")}
        </Title>
      );
    }
    // 強調（**text**）
    const boldReplaced = line.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    // リスト
    if (line.startsWith("- ")) {
      return (
        <div
          key={index}
          style={{ marginBottom: 4, paddingLeft: 16 }}
          dangerouslySetInnerHTML={{
            __html: `• ${boldReplaced.replace("- ", "")}`,
          }}
        />
      );
    }
    if (line.match(/^\d+\. /)) {
      return (
        <div
          key={index}
          style={{ marginBottom: 4, paddingLeft: 16 }}
          dangerouslySetInnerHTML={{ __html: boldReplaced }}
        />
      );
    }
    // 空行
    if (line.trim() === "") {
      return <br key={index} />;
    }
    // 通常行
    return (
      <div
        key={index}
        style={{ marginBottom: 4 }}
        dangerouslySetInnerHTML={{ __html: boldReplaced }}
      />
    );
  });
}

export const AnnouncementDetailModal: React.FC<
  AnnouncementDetailModalProps
> = ({ announcement, open, onClose }) => {
  if (!announcement) {
    return null;
  }

  return (
    <Modal
      title={
        <span>
          {announcement.title}
          <Tag
            color={getSeverityTagColor(announcement.severity)}
            style={{ marginLeft: 8 }}
          >
            {getSeverityLabel(announcement.severity)}
          </Tag>
        </span>
      }
      open={open}
      onCancel={onClose}
      footer={null}
      width="95vw"
      style={{ maxWidth: 900 }}
      styles={{
        body: {
          maxHeight: "90vh",
          overflowY: "auto",
        },
      }}
    >
      <Text type="secondary" style={{ fontSize: 12 }}>
        公開日: {formatDate(announcement.publishFrom)}
        {announcement.publishTo && (
          <> 〜 {formatDate(announcement.publishTo)}</>
        )}
      </Text>
      <Divider style={{ margin: "12px 0" }} />
      <div>{renderMarkdownSimple(announcement.bodyMd)}</div>
    </Modal>
  );
};
