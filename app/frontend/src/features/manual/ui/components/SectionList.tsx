/**
 * SectionList UI Component
 * セクション項目リストを表示する
 *
 * FSD + MVVM準拠：
 * - 純UIコンポーネント
 * - クリック時のコールバックを受け取る
 */
import React from "react";
import { Badge, Space } from "antd";
import type { SectionNavItem } from "../../domain/types/sectionNav.types";
import styles from "./SectionList.module.css";

export interface SectionListProps {
  /** セクション項目 */
  items: SectionNavItem[];
  /** 項目クリック時の処理 */
  onItemClick: (item: SectionNavItem) => void;
}

/**
 * SectionList Component
 */
export const SectionList: React.FC<SectionListProps> = ({
  items,
  onItemClick,
}) => {
  return (
    <div className={styles.list}>
      {items.map((item) => (
        <button
          key={item.id}
          className={styles.item}
          onClick={() => onItemClick(item)}
          aria-label={`${item.label}へ移動`}
        >
          <Space align="center" size={8}>
            {item.icon}
            <span className={styles.label}>{item.label}</span>
            {item.count !== undefined && (
              <Badge
                size="small"
                count={item.count}
                style={{ backgroundColor: "var(--ant-color-primary)" }}
              />
            )}
          </Space>
        </button>
      ))}
    </div>
  );
};
