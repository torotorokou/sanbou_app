/**
 * WipNotice Component
 * 開発中（Work In Progress）機能を示す汎用警告バナー
 *
 * 任意のページや機能で利用可能な共通コンポーネント
 */

import React from "react";
import { Alert } from "antd";
import { ExclamationCircleOutlined } from "@ant-design/icons";

export type WipNoticeProps = {
  /**
   * 警告を表示するかどうか
   * true = 表示、false = 非表示
   */
  show?: boolean;
  /**
   * カスタムメッセージ（オプション）
   */
  message?: string;
  /**
   * カスタム説明文（オプション）
   */
  description?: string;
  /**
   * Alert type (オプション)
   * デフォルト: "warning"
   */
  type?: "info" | "success" | "warning" | "error";
  /**
   * 閉じるボタンを表示するかどうか（オプション）
   * デフォルト: false
   */
  closable?: boolean;
};

/**
 * 開発中機能を示す汎用警告バナー
 * feature層から呼び出して、オンオフを制御可能
 *
 * @example
 * ```tsx
 * <WipNotice
 *   show={true}
 *   message="開発中の機能です"
 *   description="この機能は現在開発中です。"
 * />
 * ```
 */
export const WipNotice: React.FC<WipNoticeProps> = ({
  show = false,
  message = "開発中の機能です",
  description = "この機能は現在開発中であり、表示されているデータはダミーデータです。",
  type = "warning",
  closable = false,
}) => {
  if (!show) {
    return null;
  }

  return (
    <Alert
      message={message}
      description={description}
      type={type}
      icon={<ExclamationCircleOutlined />}
      showIcon
      closable={closable}
      style={{
        marginBottom: 16,
        borderRadius: 6,
      }}
    />
  );
};
