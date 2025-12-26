/**
 * ComingSoonPanel - 準備中機能を示すインラインパネル
 *
 * @module shared/ui/ComingSoonPanel
 *
 * Feature Flag で OFF になっている部品機能の代わりに表示する。
 * モーダルで追い返すのではなく、インラインで「準備中」を示す。
 *
 * 使用例:
 * ```tsx
 * {vm.showVideo ? (
 *   <VideoPlayer src={video.url} />
 * ) : (
 *   <ComingSoonPanel
 *     title="動画機能"
 *     description="動画再生機能は現在準備中です。近日中に公開予定です。"
 *   />
 * )}
 * ```
 */

import React from "react";
import { Alert } from "antd";
import { ClockCircleOutlined } from "@ant-design/icons";

export interface ComingSoonPanelProps {
  /**
   * 機能名
   */
  title?: string;

  /**
   * 説明文
   */
  description?: string;

  /**
   * Alert type (オプション)
   * デフォルト: "info"
   */
  type?: "info" | "warning";

  /**
   * カスタムスタイル (オプション)
   */
  style?: React.CSSProperties;
}

/**
 * 準備中機能を示すインラインパネル
 *
 * ページ内の特定セクションが未実装の場合に使用する。
 * ユーザーをページから追い出さず、他の機能は使えることを示す。
 */
export const ComingSoonPanel: React.FC<ComingSoonPanelProps> = ({
  title = "準備中",
  description = "この機能は現在準備中です。近日中に公開予定ですので、今しばらくお待ちください。",
  type = "info",
  style,
}) => {
  return (
    <Alert
      type={type}
      showIcon
      icon={<ClockCircleOutlined />}
      message={title}
      description={description}
      style={{
        margin: "16px 0",
        ...style,
      }}
    />
  );
};
