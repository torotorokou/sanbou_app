/**
 * WipNotice Component
 * 搬入量予測の開発中（Work In Progress）を示す警告バナー
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
};

/**
 * 搬入量予測が未完成であることを示す警告バナー
 * feature層から呼び出して、オンオフを制御可能
 */
export const WipNotice: React.FC<WipNoticeProps> = ({ 
  show = false, 
  message = "開発中の機能です",
  description = "搬入量予測（P50 / P10–P90）は現在開発中であり、表示されているデータはダミーデータです。"
}) => {
  if (!show) {
    return null;
  }

  return (
    <Alert
      message={message}
      description={description}
      type="warning"
      icon={<ExclamationCircleOutlined />}
      showIcon
      closable={false}
      style={{ 
        marginBottom: 16,
        borderRadius: 6,
      }}
    />
  );
};
