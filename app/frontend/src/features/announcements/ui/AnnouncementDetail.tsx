/**
 * AnnouncementDetail - お知らせ詳細UI
 *
 * お知らせの詳細を表示するコンポーネント。
 * 状態レス：propsのみで動作。
 */

import React from "react";
import { Card, Tag, Typography, Divider, Space } from "antd";
import {
  CalendarOutlined,
  PaperClipOutlined,
  FilePdfOutlined,
  LinkOutlined,
  BellOutlined,
  MailOutlined,
  MessageOutlined,
  MobileOutlined,
} from "@ant-design/icons";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeSanitize from "rehype-sanitize";
import type { Announcement, NotificationChannel } from "../domain/announcement";

const { Title, Text } = Typography;

interface AnnouncementDetailProps {
  /** 表示するお知らせ */
  announcement: Announcement;
  /** モバイルモード */
  isMobile?: boolean;
  /** タグを表示するかどうか */
  showTags?: boolean;
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
 * 通知チャネルのラベルとアイコンを取得
 */
function getChannelDisplay(channel: NotificationChannel): {
  label: string;
  icon: React.ReactNode;
} {
  switch (channel) {
    case "inApp":
      return { label: "アプリ内", icon: <MobileOutlined /> };
    case "email":
      return { label: "メール", icon: <MailOutlined /> };
    case "line":
      return { label: "LINE", icon: <MessageOutlined /> };
  }
}

/**
 * Markdownレンダリング用のスタイル
 */
const markdownStyles: React.CSSProperties = {
  lineHeight: "1.8",
  fontSize: "inherit",
  color: "inherit",
};

/**
 * Markdownレンダリング用のカスタムコンポーネントを生成
 */
const createMarkdownComponents = (isMobile: boolean) => ({
  // 見出し
  h1: ({ children, ...props }: React.HTMLAttributes<HTMLHeadingElement>) => (
    <Title
      level={isMobile ? 3 : 2}
      style={{
        marginTop: isMobile ? 16 : 24,
        marginBottom: isMobile ? 12 : 16,
      }}
      {...props}
    >
      {children}
    </Title>
  ),
  h2: ({ children, ...props }: React.HTMLAttributes<HTMLHeadingElement>) => (
    <Title
      level={isMobile ? 4 : 3}
      style={{
        marginTop: isMobile ? 14 : 20,
        marginBottom: isMobile ? 10 : 12,
      }}
      {...props}
    >
      {children}
    </Title>
  ),
  h3: ({ children, ...props }: React.HTMLAttributes<HTMLHeadingElement>) => (
    <Title
      level={isMobile ? 5 : 4}
      style={{ marginTop: isMobile ? 12 : 16, marginBottom: isMobile ? 8 : 10 }}
      {...props}
    >
      {children}
    </Title>
  ),
  h4: ({ children, ...props }: React.HTMLAttributes<HTMLHeadingElement>) => (
    <Title
      level={5}
      style={{ marginTop: isMobile ? 10 : 14, marginBottom: isMobile ? 6 : 8 }}
      {...props}
    >
      {children}
    </Title>
  ),
  // 段落
  p: ({ children, ...props }: React.HTMLAttributes<HTMLParagraphElement>) => (
    <p
      style={{ marginBottom: isMobile ? 10 : 12, lineHeight: "1.8" }}
      {...props}
    >
      {children}
    </p>
  ),
  // リンク
  a: ({
    children,
    href,
    ...props
  }: React.AnchorHTMLAttributes<HTMLAnchorElement>) => (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      style={{ color: "#1890ff", textDecoration: "underline" }}
      {...props}
    >
      {children}
    </a>
  ),
  // リスト
  ul: ({ children, ...props }: React.HTMLAttributes<HTMLUListElement>) => (
    <ul
      style={{
        marginBottom: isMobile ? 10 : 12,
        paddingLeft: isMobile ? 20 : 24,
      }}
      {...props}
    >
      {children}
    </ul>
  ),
  ol: ({ children, ...props }: React.HTMLAttributes<HTMLOListElement>) => (
    <ol
      style={{
        marginBottom: isMobile ? 10 : 12,
        paddingLeft: isMobile ? 20 : 24,
      }}
      {...props}
    >
      {children}
    </ol>
  ),
  li: ({ children, ...props }: React.HTMLAttributes<HTMLLIElement>) => (
    <li style={{ marginBottom: 6, lineHeight: "1.6" }} {...props}>
      {children}
    </li>
  ),
  // コードブロック
  code: ({
    children,
    className,
    ...props
  }: React.HTMLAttributes<HTMLElement> & { className?: string }) => {
    const isInline = !className;
    return isInline ? (
      <code
        style={{
          backgroundColor: "#f5f5f5",
          padding: "2px 6px",
          borderRadius: 3,
          fontSize: isMobile ? "0.85em" : "0.9em",
          fontFamily: 'Monaco, Consolas, "Courier New", monospace',
        }}
        {...props}
      >
        {children}
      </code>
    ) : (
      <code
        style={{
          display: "block",
          backgroundColor: "#f5f5f5",
          padding: isMobile ? 8 : 12,
          borderRadius: 6,
          fontSize: isMobile ? "0.85em" : "0.9em",
          fontFamily: 'Monaco, Consolas, "Courier New", monospace',
          overflowX: "auto",
          marginBottom: isMobile ? 10 : 12,
        }}
        {...props}
      >
        {children}
      </code>
    );
  },
  // 引用
  blockquote: ({
    children,
    ...props
  }: React.HTMLAttributes<HTMLQuoteElement>) => (
    <blockquote
      style={{
        borderLeft: "4px solid #d9d9d9",
        paddingLeft: isMobile ? 12 : 16,
        marginLeft: 0,
        marginBottom: isMobile ? 10 : 12,
        color: "#595959",
        fontStyle: "italic",
      }}
      {...props}
    >
      {children}
    </blockquote>
  ),
  // 水平線
  hr: ({ ...props }: React.HTMLAttributes<HTMLHRElement>) => (
    <Divider style={{ margin: isMobile ? "12px 0" : "16px 0" }} {...props} />
  ),
  // テーブル
  table: ({ children, ...props }: React.HTMLAttributes<HTMLTableElement>) => (
    <div style={{ overflowX: "auto", marginBottom: isMobile ? 12 : 16 }}>
      <table
        style={{
          width: "100%",
          borderCollapse: "collapse",
          fontSize: isMobile ? "0.85em" : "0.95em",
        }}
        {...props}
      >
        {children}
      </table>
    </div>
  ),
  th: ({ children, ...props }: React.HTMLAttributes<HTMLTableCellElement>) => (
    <th
      style={{
        backgroundColor: "#fafafa",
        border: "1px solid #d9d9d9",
        padding: isMobile ? "6px 8px" : "8px 12px",
        textAlign: "left",
        fontWeight: 600,
      }}
      {...props}
    >
      {children}
    </th>
  ),
  td: ({ children, ...props }: React.HTMLAttributes<HTMLTableCellElement>) => (
    <td
      style={{
        border: "1px solid #d9d9d9",
        padding: isMobile ? "6px 8px" : "8px 12px",
      }}
      {...props}
    >
      {children}
    </td>
  ),
  // 画像
  img: ({ src, alt, ...props }: React.ImgHTMLAttributes<HTMLImageElement>) => (
    <img
      src={src}
      alt={alt}
      style={{
        maxWidth: "100%",
        height: "auto",
        borderRadius: 6,
        marginBottom: isMobile ? 10 : 12,
      }}
      {...props}
    />
  ),
});

export const AnnouncementDetail: React.FC<AnnouncementDetailProps> = ({
  announcement,
  isMobile = false,
  showTags = true,
}) => {
  return (
    <Card
      className="no-hover"
      style={{ margin: "0 auto" }}
      styles={{
        body: {
          padding: isMobile ? "16px" : "24px",
        },
      }}
    >
      {/* ヘッダー */}
      <Space
        direction="vertical"
        size={isMobile ? 8 : 12}
        style={{ width: "100%" }}
      >
        {isMobile ? (
          // モバイル：センター表示
          <>
            <Title level={3} style={{ margin: 0, textAlign: "center" }}>
              {announcement.title}
            </Title>
            {showTags && (
              <div
                style={{
                  display: "flex",
                  justifyContent: "center",
                  gap: 8,
                  flexWrap: "wrap",
                }}
              >
                <Tag
                  color={getSeverityTagColor(announcement.severity)}
                  style={{ fontSize: 11 }}
                >
                  {getSeverityLabel(announcement.severity)}
                </Tag>
              </div>
            )}
          </>
        ) : (
          // デスクトップ：横並び
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 12,
              flexWrap: "wrap",
            }}
          >
            <Title level={2} style={{ margin: 0, flex: 1 }}>
              {announcement.title}
            </Title>
            {showTags && (
              <Space>
                <Tag
                  color={getSeverityTagColor(announcement.severity)}
                  style={{ fontSize: 13 }}
                >
                  {getSeverityLabel(announcement.severity)}
                </Tag>
              </Space>
            )}
          </div>
        )}

        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <CalendarOutlined
            style={{ color: "#8c8c8c", fontSize: isMobile ? 12 : 14 }}
          />
          <Text type="secondary" style={{ fontSize: isMobile ? 12 : 13 }}>
            公開日: {formatDate(announcement.publishFrom)}
            {announcement.publishTo && (
              <> 〜 {formatDate(announcement.publishTo)}</>
            )}
          </Text>
        </div>
      </Space>

      <Divider style={{ margin: isMobile ? "16px 0" : "20px 0" }} />

      {/* 本文 */}
      <div
        style={{
          fontSize: isMobile ? 14 : 15,
          color: "#262626",
          ...markdownStyles,
        }}
      >
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          rehypePlugins={[rehypeSanitize]}
          components={createMarkdownComponents(isMobile)}
        >
          {announcement.bodyMd}
        </ReactMarkdown>
      </div>

      {/* 添付ファイルセクション */}
      {announcement.attachments && announcement.attachments.length > 0 && (
        <>
          <Divider style={{ margin: isMobile ? "16px 0" : "20px 0" }} />
          <div>
            <Title
              level={5}
              style={{
                margin: 0,
                marginBottom: 12,
                display: "flex",
                alignItems: "center",
                gap: 8,
              }}
            >
              <PaperClipOutlined />
              添付ファイル
            </Title>
            <Space direction="vertical" size={8} style={{ width: "100%" }}>
              {announcement.attachments.map((attachment, index) => (
                <a
                  key={index}
                  href={attachment.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                    padding: "8px 12px",
                    backgroundColor: "#f5f5f5",
                    borderRadius: 6,
                    textDecoration: "none",
                    color: "#1890ff",
                    transition: "background-color 0.2s",
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = "#e6f7ff";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = "#f5f5f5";
                  }}
                >
                  {attachment.kind === "pdf" ? (
                    <FilePdfOutlined
                      style={{ fontSize: 16, color: "#cf1322" }}
                    />
                  ) : (
                    <LinkOutlined style={{ fontSize: 16 }} />
                  )}
                  <span style={{ flex: 1 }}>{attachment.label}</span>
                  {attachment.kind === "pdf" && (
                    <Tag color="red" style={{ margin: 0, fontSize: 10 }}>
                      PDF
                    </Tag>
                  )}
                </a>
              ))}
            </Space>
          </div>
        </>
      )}
    </Card>
  );
};
