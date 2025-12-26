/**
 * StickyManualTitleBar UI Component
 * モバイルで現在表示中のマニュアルセクションタイトルを上部に固定表示
 *
 * FSD + MVVM準拠：
 * - 純UIコンポーネント（状態管理なし）
 * - props経由でタイトルを受け取る
 * - position: sticky で固定
 */
import React from "react";
import { Typography } from "antd";
import styles from "./StickyManualTitleBar.module.css";

const { Text } = Typography;

export interface StickyManualTitleBarProps {
  /** 表示するタイトル */
  title: string;
  /** 表示するかどうか */
  show?: boolean;
}

/**
 * StickyManualTitleBar Component
 */
export const StickyManualTitleBar: React.FC<StickyManualTitleBarProps> = ({
  title,
  show = true,
}) => {
  if (!show || !title) {
    return null;
  }

  return (
    <div
      className={styles.stickyBar}
      role="status"
      aria-live="polite"
      aria-label={`現在表示中: ${title}`}
    >
      <Text strong className={styles.title}>
        {title}
      </Text>
    </div>
  );
};
