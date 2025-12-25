/**
 * AnnouncementList - お知らせ一覧UI
 *
 * お知らせ一覧を表示するコンポーネント（カード型）。
 * 重要・注意セクションとその他セクションに分けて表示。
 * 状態レス：propsのみで動作。
 */

import React from "react";
import { Empty, Typography } from "antd";
import type { AnnouncementDisplayItem } from "../model/useAnnouncementsListViewModel";
import { AnnouncementListItem } from "./AnnouncementListItem";

const { Title } = Typography;

interface AnnouncementListProps {
  /** 重要・注意アイテム */
  importantItems: AnnouncementDisplayItem[];
  /** その他アイテム */
  otherItems: AnnouncementDisplayItem[];
  /** 詳細を開くコールバック */
  onOpen: (id: string) => void;
  /** モバイルモード */
  isMobile?: boolean;
}

export const AnnouncementList: React.FC<AnnouncementListProps> = ({
  importantItems,
  otherItems,
  onOpen,
  isMobile = false,
}) => {
  // 空状態
  if (importantItems.length === 0 && otherItems.length === 0) {
    return (
      <Empty description="お知らせはありません" style={{ padding: "40px 0" }} />
    );
  }

  return (
    <div>
      {/* 重要・注意セクション */}
      {importantItems.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <Title level={5} style={{ marginBottom: 10, color: "#8c8c8c" }}>
            重要なお知らせ（{importantItems.length}）
          </Title>
          {importantItems.map((item) => (
            <AnnouncementListItem
              key={item.id}
              item={item}
              onOpen={onOpen}
              isMobile={isMobile}
            />
          ))}
        </div>
      )}

      {/* その他セクション */}
      {otherItems.length > 0 && (
        <div>
          <Title level={5} style={{ marginBottom: 10, color: "#8c8c8c" }}>
            一般のお知らせ（{otherItems.length}）
          </Title>
          {otherItems.map((item) => (
            <AnnouncementListItem
              key={item.id}
              item={item}
              onOpen={onOpen}
              isMobile={isMobile}
            />
          ))}
        </div>
      )}
    </div>
  );
};
